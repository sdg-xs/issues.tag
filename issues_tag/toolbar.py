"""Issues entry beside Section Box on Kit's main toolbar."""
from pathlib import Path

import omni.kit.widget.toolbar as toolbar_module
import omni.ui as ui


class IssuesToolbarButton(toolbar_module.WidgetGroup):
    def __init__(self, on_open):
        super().__init__()
        self._on_open = on_open
        self.button = None
        self._toolbar = toolbar_module.get_instance()
        if self._toolbar:
            self._toolbar.add_widget(self, priority=901)

    def get_style(self):
        icon = Path(__file__).resolve().parent.parent / 'data' / 'issues.svg'
        return {'Button.Image::issues_open': {'image_url': str(icon)}}

    def create(self, default_size):
        self.button = ui.Button(name='issues_open', tooltip='Open Issues',
                                width=default_size, height=default_size,
                                clicked_fn=self._open)
        return {'issues_open': self.button}

    def _open(self):
        if self._on_open:
            self._on_open()

    def destroy(self):
        toolbar, self._toolbar = self._toolbar, None
        self._on_open = None
        try:
            if toolbar:
                toolbar.remove_widget(self)
        finally:
            self.button = None
            self.clean()
