"""Lifecycle and the Issues menu entry."""
import omni.ext
from omni.kit.menu.utils import MenuItemDescription, add_menu_items, remove_menu_items

from .service import IssueService

_service = None


def get_runtime_service():
    return _service


class IssuesExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        global _service
        self._service = IssueService()
        _service = self._service
        self._window = None
        self._menus = [MenuItemDescription(name="Issues", onclick_fn=self.show)]
        add_menu_items(self._menus, "Window")

    def show(self):
        if self._window is None:
            from .window import IssuesWindow
            self._window = IssuesWindow(self._service)
        self._window.show()

    def on_shutdown(self):
        global _service
        remove_menu_items(self._menus, "Window")
        if self._window is not None:
            self._window.destroy()
        self._window = None
        self._service.destroy()
        if _service is self._service:
            _service = None
        self._service = None
