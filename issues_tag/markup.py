"""Editable evidence through NVIDIA's supported Markup Core API."""
import asyncio
import io
import tempfile
from pathlib import Path
from dataclasses import replace
from uuid import uuid4

import omni.kit.app
from pxr import Usd


class MarkupAdapter:
    def __init__(self, service):
        self.service = service
        self.core = None
        self._editing = None
        self._root_target = None
        self._stage = None
        self._busy = False
        self._editing_id = None

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
        self.service.store.require_writable()
        record = self.service.viewport.capture()
        await self._ready()
        self._same_scene(stage, generation)
        old_target = stage.GetEditTarget()
        stage.SetEditTarget(stage.GetRootLayer())
        try:
            name = 'IssueEvidence_' + uuid4().hex
            from omni.kit.markup.core import MarkupChangeCallbacks
            created = asyncio.get_running_loop().create_future()
            def on_created(*args):
                owned = self.core.get_markup(name)
                if owned and owned.thumbnail_data and not created.done():
                    created.set_result(owned)
            callback = MarkupChangeCallbacks(on_markup_created=on_created)
            self.core.register_callback(callback)
            try:
                self.core.create_markup('/Viewport_Markups/' + name)
                markup = await asyncio.wait_for(created, 30)
            finally:
                self.core.deregister_callback(callback)
            self._same_scene(stage, generation)
            self.core.end_edit_markup(markup, update_thumbnail=False)
            self.core.unlock_camera()
            data = await self._snapshot(markup, stage, generation)
            return replace(record, markup_path=markup.path, snapshot=data)
        finally:
            if self.service.stage == stage:
                self.core.unlock_camera()
                self.core.current_markup = None
                stage.SetEditTarget(old_target)

    async def ensure_editable(self, record):
        if record.markup_path:
            return record
        evidence = await self.capture_viewpoint()
        return replace(record, markup_path=evidence.markup_path, snapshot=evidence.snapshot)

    async def _snapshot(self, markup, stage, generation):
        from PIL import Image
        import omni.appwindow
        import omni.kit.renderer_capture
        import omni.kit.viewport.utility as viewport_util
        import omni.ui as ui
        window = viewport_util.get_active_viewport_window('Viewport')
        if not window or not window.visible:
            raise ValueError('Markup evidence requires the visible primary Viewport window.')
        await asyncio.wait_for(viewport_util.next_viewport_frame_async(window.viewport_api, 1), 30)
        self._same_scene(stage, generation)
        renderer = omni.kit.renderer_capture.acquire_renderer_capture_interface()
        app_window = omni.appwindow.get_default_app_window()
        with tempfile.TemporaryDirectory(prefix='issues-capture-') as directory:
            path = Path(directory) / 'evidence.png'
            renderer.capture_next_frame_swapchain_to_file(str(path), app_window, {'format': 'png'})
            await omni.kit.app.get_app().next_update_async()
            renderer.wait_async_capture(app_window)
            for _ in range(60):
                self._same_scene(stage, generation)
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
            await self._ready()
            self._same_scene(stage, generation)
            self.service.store.require_writable()
            self._root_target = stage.GetEditTarget()
            self._stage = stage
            stage.SetEditTarget(stage.GetRootLayer())
            markup = self.core.get_markup_from_prim_path(record.markup_path)
            if not markup:
                raise ValueError('This viewpoint has no editable Markup in the current scene.')
            self.core.recall_markup(markup, without_camera=True, force=True)
            self.core.begin_edit_markup(markup)
            self.service.viewport.restore(record)
            self._editing = markup
            self._editing_id = record.id
            return markup
        except BaseException:
            if self._root_target and self.service.stage == self._stage:
                stage.SetEditTarget(self._root_target)
            self._stage = self._root_target = None
            self._busy = False
            raise

    async def finish(self, record, save=True):
        stage, generation = self.service.stage, self.service.generation
        markup = self._editing
        if not markup or stage != self._stage or record.id != self._editing_id:
            raise ValueError('The annotation scene changed.')
        try:
            import importlib
            tool = importlib.import_module('omni.kit.tool.markup').get_instance()
            if tool:
                tool.refresh_elements(refresh_all_elements=True)
            for _ in range(5):
                await omni.kit.app.get_app().next_update_async()
            self._same_scene(stage, generation)
            self.core.end_edit_markup(markup, save=save, update_thumbnail=False)
            data = await self._snapshot(markup, stage, generation) if save else record.snapshot
            return replace(record, snapshot=data)
        finally:
            self.core.unlock_camera()
            self.core.current_markup = None
            self._editing = None
            self._editing_id = None
            self._busy = False
            if self.service.stage == self._stage:
                stage.SetEditTarget(self._root_target)
            self._root_target = None
            self._stage = None

    def destroy(self):
        if self.core:
            if self._editing and self.service.stage == self._stage:
                self.core.end_edit_markup(self._editing, save=False, update_thumbnail=False)
                self._stage.SetEditTarget(self._root_target)
            self.core.unlock_camera()
        self._editing = None
        self._editing_id = None
        self._busy = False
        self.core = None
