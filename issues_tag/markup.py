"""Editable evidence through NVIDIA's supported Markup Core API."""
import asyncio
import io
import tempfile
from pathlib import Path
from dataclasses import replace
from uuid import uuid4
from weakref import WeakKeyDictionary, ref

import omni.kit.app
from pxr import Usd


_root_targets = WeakKeyDictionary()


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

    async def capture_viewpoint(self):
        if self._busy:
            raise ValueError('Finish or cancel the current annotation before capturing another view.')
        self._busy = True
        try:
            return await self._capture_viewpoint()
        finally:
            self._busy = False

    async def _capture_viewpoint(self):
        stage, generation = self.service.stage, self.service.generation
        context = self.service._context
        self.service.store.require_writable()
        window, viewport = self._evidence_viewport()
        await self._ready()
        self._same_scene(stage, generation)
        core = self.core
        record = viewport.capture()
        target_lease = _RootTargetLease(self.service, core)
        markup = None
        try:
            name = 'IssueEvidence_' + uuid4().hex
            from omni.kit.markup.core import MarkupChangeCallbacks
            created = asyncio.get_running_loop().create_future()
            def on_created(*args):
                owned = core.get_markup(name)
                if owned and owned.thumbnail_data and not created.done():
                    created.set_result(owned)
            callback = MarkupChangeCallbacks(on_markup_created=on_created)
            core.register_callback(callback)
            try:
                core.create_markup('/Viewport_Markups/' + name)
                markup = core.get_markup(name)
                markup = await asyncio.wait_for(created, 30)
            finally:
                core.deregister_callback(callback)
            self._require_owner(markup, stage, generation)
            self.core.end_edit_markup(markup, update_thumbnail=False)
            data = await self._snapshot(markup, stage, generation, window)
            return replace(record, markup_path=markup.path, snapshot=data)
        finally:
            try:
                if context.get_stage() == stage and self.service.generation == generation and markup:
                    if core.editing_markup == markup:
                        core.end_edit_markup(markup, save=True, update_thumbnail=False)
                    if core.current_markup == markup:
                        core.unlock_camera()
                        core.current_markup = None
            finally:
                target_lease.release()

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
        if self._busy:
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
        self._release_edit(cancel=True)
        self.core = None
