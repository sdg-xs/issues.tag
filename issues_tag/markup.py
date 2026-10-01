"""Editable evidence through NVIDIA's supported Markup Core API."""
import asyncio
from contextlib import nullcontext
import io
import math
import tempfile
from pathlib import Path
from dataclasses import replace
from uuid import uuid4
from weakref import WeakKeyDictionary, ref

import omni.kit.app
from pxr import Usd, UsdGeom


_root_targets = WeakKeyDictionary()


def _native_camera_matches(saved_prim, destination, record):
    """Evaluate the vendor's attribute-copy result without changing the live scene."""
    try:
        # Vendor recall writes defaults and leaves destination animation samples intact.
        if any(attr.GetNumTimeSamples() for attr in destination.GetAttributes()):
            return False
        scratch = Usd.Stage.CreateInMemory()
        camera = UsdGeom.Camera.Define(scratch, '/Camera')
        for source in (destination, saved_prim):
            for attr in source.GetAttributes():
                value = attr.Get()
                if value is not None:
                    camera.GetPrim().CreateAttribute(attr.GetName(), attr.GetTypeName()).Set(value)
        matrix = camera.GetLocalTransformation()
        actual = {
            'transform': [float(matrix[r][c]) for r in range(4) for c in range(4)],
            'horizontal_aperture': float(camera.GetHorizontalApertureAttr().Get()),
            'vertical_aperture': float(camera.GetVerticalApertureAttr().Get()),
            'focal_length': float(camera.GetFocalLengthAttr().Get()),
            'clipping_range': list(camera.GetClippingRangeAttr().Get()),
        }
        if str(camera.GetProjectionAttr().Get()) != record.camera['projection']:
            return False
        for key, received in actual.items():
            wanted = record.camera[key]
            if isinstance(received, list):
                if len(received) != len(wanted) or any(not math.isclose(a, b, rel_tol=0, abs_tol=1e-6) for a, b in zip(received, wanted)):
                    return False
            elif not math.isclose(received, wanted, rel_tol=0, abs_tol=1e-6):
                return False
        return True
    except Exception:
        return False


class _RootTargetState:
    def __init__(self, service, core):
        self.service = ref(service)
        self.core = core
        self.context = service._context
        self.stage = service.stage
        self.generation = service.generation
        self.original = self.stage.GetEditTarget()
        self.imposed = Usd.EditTarget(self.stage.GetRootLayer())
        self.users = 0
        self.watch = None

    def restore(self, event=None):
        service = self.service()
        same_scene = self.context.get_stage() == self.stage and (not service or service.generation == self.generation)
        if self.users:
            self.watch = None
            return
        if same_scene and self.stage.GetEditTarget() == self.imposed and self.core.editing_markup:
            if not self.watch:
                self.watch = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(
                    self.restore, name='issues.markup.edit_target')
            return
        try:
            if same_scene and self.stage.GetEditTarget() == self.imposed:
                self.stage.SetEditTarget(self.original)
        finally:
            if service and _root_targets.get(service) is self:
                del _root_targets[service]
            self.watch = None


class _RootTargetLease:
    def __init__(self, service, core):
        state = _root_targets.get(service)
        if not state or state.stage != service.stage or state.generation != service.generation:
            state = _RootTargetState(service, core)
            _root_targets[service] = state
        elif state.stage.GetEditTarget() != state.imposed:
            state.original = state.stage.GetEditTarget()
        state.stage.SetEditTarget(state.imposed)
        state.users += 1
        state.watch = None
        self.state = state

    def release(self):
        state, self.state = self.state, None
        if state:
            state.users -= 1
            state.restore()


class MarkupAdapter:
    def __init__(self, service):
        self.service = service
        self.core = None
        self._editing = None
        self._target_lease = None
        self._stage = None
        self._busy = False
        self._editing_id = None
        self._window = None
        self._generation = None
        self._editing_active = False
        self._capture_task = None
        self._capture_cancel_requested = False
        self._captured_drafts = {}
        self._unsettled_drafts = set()
        self._destroyed = False
        self.suppress_window_close = lambda windows: nullcontext()
        self._capturing_path = ''
        self._draft_generation = service.generation

    def _release_edit(self, cancel=False):
        same_scene = self.service.stage == self._stage and self.service.generation == self._generation
        owned = self.core and self._editing and self.core.current_markup == self._editing
        try:
            if same_scene and self.core and self._editing:
                try:
                    if cancel and self._editing_active and self.core.editing_markup == self._editing:
                        self.core.end_edit_markup(self._editing, save=not owned, update_thumbnail=False)
                finally:
                    if owned and (self.core.current_markup is None or self.core.current_markup == self._editing):
                        self.core.unlock_camera()
                        self.core.current_markup = None
        finally:
            try:
                if self._target_lease:
                    self._target_lease.release()
            finally:
                self._editing = None
                self._editing_id = None
                self._editing_active = False
                self._busy = False
                self._stage = self._target_lease = self._window = self._generation = None

    def _evidence_viewport(self):
        import omni.kit.viewport.utility as viewport_util
        from .viewport import ViewportAdapter
        window = viewport_util.get_active_viewport_window('Viewport')
        if not window or not window.visible or self.service.viewport.viewport != window.viewport_api:
            raise ValueError('Select the visible primary Viewport before capturing or editing Markup evidence.')
        if window.viewport_api.stage != self.service.stage:
            raise ValueError('The primary Viewport must show the current scene.')
        return window, ViewportAdapter(self.service, window.viewport_api)

    async def _ready(self):
        import importlib
        manager = omni.kit.app.get_app().get_extension_manager()
        for name in ('omni.kit.markup.core', 'omni.kit.tool.markup'):
            if not manager.is_extension_enabled(name):
                manager.set_extension_enabled_immediate(name, True)
        self.core = importlib.import_module('omni.kit.markup.core').get_instance()
        for _ in range(8):
            await omni.kit.app.get_app().next_update_async()
        if not self.core:
            raise ValueError('Markup Core is unavailable in this Kit installation.')

    def _same_scene(self, stage, generation):
        if self.service.stage != stage or self.service.generation != generation:
            raise ValueError('The scene changed; the evidence capture was discarded.')

    def _require_owner(self, markup, stage, generation):
        self._same_scene(stage, generation)
        if not self.core or self.core.current_markup != markup:
            raise ValueError('The NVIDIA Markup selection changed; the evidence was discarded.')

    def restore_viewpoint(self, record):
        """Recall an existing native camera without entering Markup review or editing."""
        if not record.markup_path:
            return False
        core = self.core
        if not core:
            manager = omni.kit.app.get_app().get_extension_manager()
            if not manager.is_extension_enabled('omni.kit.markup.core'):
                return False
            import importlib
            core = importlib.import_module('omni.kit.markup.core').get_instance()
        if not core:
            return False
        if self._busy or core.editing_markup or core.current_markup:
            raise ValueError('Finish or close the current Markup review before opening another saved view.')
        markup = core.get_markup_from_prim_path(record.markup_path)
        stage = self.service.stage
        if not markup or markup.path != record.markup_path or not markup.usd_prim or markup.usd_prim.GetStage() != stage:
            return False
        if not markup.camera_prim or markup.camera_prim.GetStage() != stage or not stage.GetPrimAtPath('/OmniverseKit_Persp'):
            return False
        try:
            window, _ = self._evidence_viewport()
        except ValueError:
            return False
        from omni.kit.viewport.window import get_viewport_window_instances
        for other_window in get_viewport_window_instances(None):
            other = other_window.viewport_api
            if other != window.viewport_api and other.stage == stage and str(other.camera_path) == '/OmniverseKit_Persp':
                return False
        if not _native_camera_matches(markup.camera_prim, stage.GetPrimAtPath('/OmniverseKit_Persp'), record):
            return False
        # The Issues record owns review context; only the native camera setting is recalled.
        self.service.viewport.restore(record, restore_camera=False)
        with Usd.EditContext(stage, stage.GetSessionLayer()):
            markup.recall(without_camera=False, disable_settings=['info', 'Approve', 'thumbnail'])
        return str(window.viewport_api.camera_path) == '/OmniverseKit_Persp'

    async def capture_viewpoint(self):
        if self._busy or (self._capture_task and not self._capture_task.done()):
            raise ValueError('Finish or cancel the current annotation before capturing another view.')
        self._busy = True
        self._capture_cancel_requested = False
        task = self._capture_task = asyncio.create_task(self._capture_viewpoint())
        try:
            try:
                return await asyncio.shield(task)
            except asyncio.CancelledError:
                self._capture_cancel_requested = True
                # Caller cancellation must not release the native capture's scene lease.
                while not task.done():
                    try:
                        await asyncio.shield(task)
                    except asyncio.CancelledError:
                        continue
                    except Exception:
                        break
                if not task.cancelled():
                    task.exception()
                raise
        finally:
            self._busy = False
            self._capture_task = None

    async def _capture_viewpoint(self):
        stage, generation = self.service.stage, self.service.generation
        if self._draft_generation != generation:
            self._captured_drafts.clear()
            self._unsettled_drafts.clear()
            self._draft_generation = generation
        context = self.service._context
        store = self.service.store
        store.require_writable()
        window, viewport = self._evidence_viewport()
        await self._ready()
        self._same_scene(stage, generation)
        if self._capture_cancel_requested:
            raise asyncio.CancelledError()
        core = self.core
        record = viewport.capture()
        target_lease = _RootTargetLease(self.service, core)
        markup = None
        settled = successful = False
        try:
            name = 'IssueEvidence_' + uuid4().hex
            from omni.kit.markup.core import MarkupChangeCallbacks
            created = asyncio.get_running_loop().create_future()
            def on_created(*args):
                owned = core.get_markup(name)
                if owned and owned.thumbnail_data and not created.done():
                    self._captured_drafts[owned.path] = generation
                    self._unsettled_drafts.add(owned.path)
                    self._capturing_path = owned.path
                    created.set_result(owned)
            callback = MarkupChangeCallbacks(on_markup_created=on_created)
            core.register_callback(callback)
            try:
                deadline = asyncio.get_running_loop().time() + 30
                core.create_markup('/Viewport_Markups/' + name)
                markup = core.get_markup(name)
                if markup:
                    self._capturing_path = markup.path
                    self._captured_drafts[markup.path] = generation
                    self._unsettled_drafts.add(markup.path)
                markup = await asyncio.wait_for(created, max(0, deadline - asyncio.get_running_loop().time()))
                # Public vendor settling convention, not a GPU completion fence.
                await asyncio.wait_for(markup.wait(), max(0, deadline - asyncio.get_running_loop().time()))
                if context.get_stage() != stage or self.service.generation != generation or window.viewport_api.stage != stage:
                    raise ValueError('The evidence viewport changed scenes; capture was discarded.')
                from omni.kit.viewport.utility import next_viewport_frame_async
                # App updates do not establish delivery by this specific viewport.
                await asyncio.wait_for(next_viewport_frame_async(window.viewport_api, 2),
                                       max(0, deadline - asyncio.get_running_loop().time()))
                if context.get_stage() != stage or self.service.generation != generation or window.viewport_api.stage != stage:
                    raise ValueError('The evidence viewport changed scenes; capture was discarded.')
                settled = True
                self._unsettled_drafts.discard(markup.path)
            finally:
                core.deregister_callback(callback)
            if self._capture_cancel_requested or self._destroyed:
                raise asyncio.CancelledError()
            self._require_owner(markup, stage, generation)
            core.end_edit_markup(markup, update_thumbnail=False)
            data = await self._snapshot(markup, stage, generation, window)
            if self._capture_cancel_requested or self._destroyed:
                raise asyncio.CancelledError()
            result = replace(record, markup_path=markup.path, snapshot=data)
            successful = True
            return result
        finally:
            try:
                if context.get_stage() == stage and self.service.generation == generation and markup:
                    if core.editing_markup == markup:
                        core.end_edit_markup(markup, save=True, update_thumbnail=False)
                    if core.current_markup == markup:
                        core.unlock_camera()
                        core.current_markup = None
            finally:
                try:
                    if settled and not successful and markup:
                        self._discard_draft(markup.path, stage, generation, core, context, store, lease_owned=True)
                finally:
                    try:
                        target_lease.release()
                    finally:
                        self._capturing_path = ''

    def discard_viewpoint(self, record, stage, generation):
        """Delete this adapter's unsaved native draft in its originating scene."""
        if self._draft_generation != self.service.generation:
            self._captured_drafts.clear()
            self._unsettled_drafts.clear()
            self._draft_generation = self.service.generation
        context, core = self.service._context, self.core
        if not context or not core or self.service.stage != stage or context.get_stage() != stage or self.service.generation != generation:
            return False
        if self._capture_task and not self._capture_task.done():
            return False
        return self._discard_draft(record.markup_path, stage, generation, core, context, self.service.store, record.id)

    def _discard_draft(self, path, stage, generation, core, context, store, view_id='', *, lease_owned=False):
        if context.get_stage() != stage or self.service.generation != generation:
            return False
        if not path.startswith('/Viewport_Markups/IssueEvidence_') or '/' in path[len('/Viewport_Markups/'):]:
            return False
        if self._captured_drafts.get(path) != generation or path in self._unsettled_drafts:
            return False
        markup = core.get_markup_from_prim_path(path)
        if not markup or markup.path != path or not markup.usd_prim or markup.usd_prim.GetStage() != stage:
            return False
        if core.editing_markup and (core.editing_markup != markup or self._editing != markup):
            return False
        if view_id:
            try:
                store.get_viewpoint(view_id)
            except KeyError:
                pass
            else:
                return False
        for issue in store.list_issues():
            view_ids = (issue.initial_viewpoint_id,) + tuple(comment.viewpoint_id for comment in issue.comments)
            for view_id in view_ids:
                if view_id and store.get_viewpoint(view_id).markup_path == path:
                    return False
        store.require_writable()
        if self._editing == markup:
            self._release_edit(cancel=True)
        lease = None if lease_owned else _RootTargetLease(self.service, core)
        try:
            if not core.can_edit_markup(markup, show_messages=False):
                raise ValueError('NVIDIA Markup refused to delete the draft evidence.')
            core.delete_markup(markup)
            if core.get_markup_from_prim_path(path) or stage.GetPrimAtPath(path):
                raise ValueError('NVIDIA Markup did not delete the draft evidence.')
            del self._captured_drafts[path]
            return True
        finally:
            if lease:
                lease.release()

    async def copy_for_edit(self, record):
        """Copy saved annotations into owned evidence; never edit the saved prim."""
        from pxr import Sdf, UsdGeom
        stage, generation = self.service.stage, self.service.generation
        self.service.restore_viewpoint(record)
        evidence = await self.capture_viewpoint()
        try:
            self._same_scene(stage, generation)
            source = stage.GetPrimAtPath(record.markup_path) if record.markup_path else None
            if source:
                flattened = stage.Flatten()
                root = stage.GetRootLayer()
                with Usd.EditContext(stage, root):
                    for child in source.GetChildren():
                        if child.IsA(UsdGeom.Camera) or child.HasAttribute('projection'):
                            continue
                        destination = Sdf.Path(evidence.markup_path).AppendChild(child.GetName())
                        if not Sdf.CopySpec(flattened, child.GetPath(), root, destination):
                            raise ValueError('The saved annotation could not be copied.')
            return replace(record, id=evidence.id, markup_path=evidence.markup_path)
        except BaseException:
            self.discard_viewpoint(evidence, stage, generation)
            raise

    async def ensure_editable(self, record):
        if record.markup_path:
            return record
        evidence = await self.capture_viewpoint()
        return replace(record, markup_path=evidence.markup_path, snapshot=evidence.snapshot)

    async def _snapshot(self, markup, stage, generation, window):
        from PIL import Image
        import omni.appwindow
        import omni.kit.renderer_capture
        import omni.kit.viewport.utility as viewport_util
        import omni.ui as ui
        if not window or not window.visible:
            raise ValueError('Markup evidence requires the visible primary Viewport window.')
        import carb.settings
        from .evidence_capture import clean_evidence_ui, overlapping_windows
        overlays = self.service.viewport.evidence_overlays(window.viewport_api)
        floating_windows = overlapping_windows(window, ui.Workspace.get_windows())
        with self.suppress_window_close(floating_windows), clean_evidence_ui(overlays, floating_windows, carb.settings.get_settings()):
            for _ in range(3):
                await omni.kit.app.get_app().next_update_async()
            await asyncio.wait_for(viewport_util.next_viewport_frame_async(window.viewport_api, 1), 30)
            self._require_owner(markup, stage, generation)
            renderer = omni.kit.renderer_capture.acquire_renderer_capture_interface()
            app_window = omni.appwindow.get_default_app_window()
            with tempfile.TemporaryDirectory(prefix='issues-capture-') as directory:
                path = Path(directory) / 'evidence.png'
                renderer.capture_next_frame_swapchain_to_file(str(path), app_window, {'format': 'png'})
                await omni.kit.app.get_app().next_update_async()
                renderer.wait_async_capture(app_window)
                for _ in range(60):
                    self._require_owner(markup, stage, generation)
                    if path.exists():
                        break
                    await omni.kit.app.get_app().next_update_async()
                if not path.exists():
                    raise ValueError('Markup capture requires a visible Kit render window.')
                image = Image.open(path).convert('RGBA')
                frame = window.get_frame('omni.kit.tool.markup')
                scale = ui.Workspace.get_dpi_scale()
                x, y, width, height = (float(frame.screen_position_x), float(frame.screen_position_y), float(frame.computed_width), float(frame.computed_height))
                if width <= 0 or height <= 0:
                    raise ValueError('The Markup drawing area is unavailable.')
                image = image.crop((round(x * scale), round(y * scale), round((x + width) * scale), round((y + height) * scale)))
                image.thumbnail((1500, 1500))
        output = io.BytesIO()
        image.save(output, format='PNG')
        return output.getvalue()

    async def begin(self, record):
        if self._busy or (self._capture_task and not self._capture_task.done()):
            raise ValueError('Finish or cancel the current annotation before opening another.')
        self._busy = True
        stage, generation = self.service.stage, self.service.generation
        try:
            window, viewport = self._evidence_viewport()
            await self._ready()
            self._same_scene(stage, generation)
            self.service.store.require_writable()
            self._target_lease = _RootTargetLease(self.service, self.core)
            self._stage = stage
            self._generation = generation
            self._window = window
            markup = self.core.get_markup_from_prim_path(record.markup_path)
            if not markup:
                raise ValueError('This viewpoint has no editable Markup in the current scene.')
            self._editing = markup
            self._editing_id = record.id
            self.core.recall_markup(markup, without_camera=True, force=True)
            self._editing_active = True
            if not self.core.begin_edit_markup(markup):
                raise ValueError('Markup could not start editing this viewpoint.')
            viewport.restore(record)
            return markup
        except BaseException:
            self._release_edit(cancel=True)
            raise

    async def finish(self, record, save=True):
        stage, generation = self.service.stage, self.service.generation
        markup = self._editing
        if stage != self._stage or generation != self._generation:
            self._release_edit(cancel=True)
            raise ValueError('The annotation scene changed.')
        if not markup or record.id != self._editing_id:
            raise ValueError('The annotation scene changed.')
        try:
            self._require_owner(markup, stage, generation)
            import importlib
            tool = importlib.import_module('omni.kit.tool.markup').get_instance()
            if tool:
                tool.refresh_elements(refresh_all_elements=True)
            for _ in range(5):
                await omni.kit.app.get_app().next_update_async()
            self._require_owner(markup, stage, generation)
            self.core.end_edit_markup(markup, save=save, update_thumbnail=False)
            self._editing_active = False
            data = await self._snapshot(markup, stage, generation, self._window) if save else record.snapshot
            return replace(record, snapshot=data)
        finally:
            self._release_edit(cancel=True)

    def destroy(self):
        self._destroyed = True
        errors = []
        try:
            try:
                self._release_edit(cancel=True)
            except Exception as error:
                errors.append(error)
            if self.core and self._captured_drafts:
                context, core = self.service._context, self.core
                stage, generation = self.service.stage, self.service.generation
                if context and stage and context.get_stage() == stage:
                    store = self.service.store
                    for path in tuple(self._captured_drafts):
                        if path == self._capturing_path:
                            continue
                        try:
                            self._discard_draft(path, stage, generation, core, context, store)
                        except Exception as error:
                            errors.append(error)
        finally:
            self.core = None
        if errors:
            raise ExceptionGroup('Native draft cleanup failed', errors)
