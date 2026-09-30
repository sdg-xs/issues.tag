"""Lifecycle and the Issues menu entry."""
import asyncio
from pathlib import Path

import omni.ext
import omni.ui as ui
from omni.kit.menu.utils import MenuItemDescription, add_menu_items, remove_menu_items

from .service import IssueService

_service = None


def get_runtime_service():
    return _service


class IssuesExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        global _service
        self._service = IssueService()
        from .viewport import ViewportAdapter
        from .markup import MarkupAdapter
        self._service.viewport = ViewportAdapter(self._service)
        self._service.viewport.start()
        self._markup = MarkupAdapter(self._service)
        self._dialogs = []
        self._tasks = set()
        self._draft_views = {}
        _service = self._service
        self._window = None
        self._menus = [MenuItemDescription(name="Issues", onclick_fn=self.show)]
        add_menu_items(self._menus, "Window")

    def show(self):
        if self._window is None:
            from .window import IssuesWindow
            self._window = IssuesWindow(self._service, on_place_pin=self.place_pin,
                on_add_viewpoint=self.capture, on_markup=self.annotate,
                on_add_related=self.add_related, on_import=lambda: self.file_dialog(False),
                on_export=lambda: self.file_dialog(True))
            self._service.viewport.on_pin_clicked = self._window.select_issue
        self._window.show()

    async def place_pin(self, issue_id=None):
        anchor = await self._service.viewport.request_placement()
        if anchor is None:
            return None
        if issue_id:
            self._service.reattach(issue_id, anchor)
        else:
            description = self._window.description.as_string.strip() or 'New issue'
            from .viewport import ViewportAdapter
            viewpoint = ViewportAdapter(self._service, self._service.viewport._placement_viewport).capture()
            issue_id = self._service.create_issue(description, anchor, viewpoint)
        self._window.select_issue(issue_id)
        return issue_id

    async def capture(self, issue_id):
        viewpoint = await self._markup.capture_viewpoint()
        self._draft_views[viewpoint.id] = viewpoint
        return viewpoint

    def add_related(self, issue_id):
        from .elements import reference_for_prim
        record = self._service.get_issue(issue_id)
        refs = tuple(reference_for_prim(self._service.stage, p)
                     for p in self._service._context.get_selection().get_selected_prim_paths())
        self._service.set_related_elements(issue_id, record.related_elements + refs)

    async def annotate(self, viewpoint_id):
        try:
            record = self._service.store.get_viewpoint(viewpoint_id)
            saved = True
        except KeyError:
            record = self._draft_views[viewpoint_id]
            saved = False
        self._service.viewport.restore(record)
        record = await self._markup.ensure_editable(record)
        await self._markup.begin(record)
        future = asyncio.get_running_loop().create_future()
        window = ui.Window('Issue annotation', width=310, height=110)
        self._dialogs.append(window)
        def complete(save):
            if not future.done():
                future.set_result(save)
        with window.frame:
            with ui.VStack(spacing=8):
                ui.Label('Draw using the Markup tools, then apply.')
                with ui.HStack():
                    ui.Button('Apply', clicked_fn=lambda: complete(True))
                    ui.Button('Cancel', clicked_fn=lambda: complete(False))
        window.set_visibility_changed_fn(lambda visible: complete(False) if not visible else None)
        try:
            save = await future
            updated = await self._markup.finish(record, save)
            if saved and save:
                self._service.mutate(lambda: self._service.store.put_viewpoint(updated))
            elif not saved:
                self._draft_views[viewpoint_id] = updated
            return updated
        finally:
            window.destroy()
            if window in self._dialogs:
                self._dialogs.remove(window)

    def file_dialog(self, export):
        from omni.kit.window.filepicker import FilePickerDialog
        from .bcf import read_bcf, write_bcf, export_document, plan_import, apply_import
        from .import_window import ImportWindow
        def selected(filename, dirname):
            path = Path(dirname) / filename
            if export:
                if path.suffix.lower() != '.bcf':
                    path = path.with_suffix('.bcf')
                write_bcf(export_document(self._service.store), path)
            else:
                plan = plan_import(read_bcf(path), self._service.store)
                preview = ImportWindow(plan, lambda choices: apply_import(plan, choices, self._service))
                self._dialogs.append(preview)
            dialog.hide()
        dialog = FilePickerDialog('Export BCF' if export else 'Import BCF', apply_button_label='Export' if export else 'Preview',
                                  click_apply_handler=lambda filename, dirname: self._window._call(selected, filename, dirname))
        self._dialogs.append(dialog)
        dialog.show()

    def on_shutdown(self):
        global _service
        remove_menu_items(self._menus, "Window")
        if self._window is not None:
            self._window.destroy()
        self._window = None
        for dialog in self._dialogs:
            dialog.destroy()
        self._dialogs.clear()
        self._markup.destroy()
        self._service.viewport.destroy()
        self._draft_views.clear()
        self._service.destroy()
        if _service is self._service:
            _service = None
        self._service = None
