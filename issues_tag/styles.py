"""Native issue-panel palette and widget states."""

from omni.ui import color as cl

BACKGROUND = cl("#141a1e")
SURFACE = cl("#20292e")
RAISED = cl("#2b373e")
TEXT = cl("#edf3f5")
MUTED = cl("#acbcc4")
ACCENT = cl("#2de1c2")
BORDER = cl("#455861")

STYLE = {
    "Window": {"background_color": BACKGROUND},
    "Label": {"color": TEXT, "font_size": 14},
    "Label::muted": {"color": MUTED, "font_size": 12},
    "Label::section": {"color": MUTED, "font_size": 13},
    "Label::heading": {"color": TEXT, "font_size": 18},
    "Label::error": {"color": cl("#ffd4cb"), "font_size": 12},
    "Button": {"background_color": SURFACE, "border_color": BORDER, "border_width": 1, "border_radius": 2},
    "Button:hovered": {"background_color": RAISED},
    "Button:pressed": {"border_color": ACCENT},
    "Button:disabled": {"background_color": BACKGROUND},
    "Button.Label": {"color": TEXT, "font_size": 13},
    "Button.Label:disabled": {"color": MUTED},
    "Button::primary": {"background_color": ACCENT, "border_radius": 2},
    "Button::primary.Label": {"color": BACKGROUND},
    "Button::selected": {"background_color": RAISED, "border_color": ACCENT, "border_width": 1},
    "StringField": {"background_color": SURFACE, "color": TEXT, "border_color": BORDER, "border_width": 1, "border_radius": 2, "font_size": 14},
    "StringField:focused": {"border_color": ACCENT},
    "StringField:disabled": {"background_color": BACKGROUND, "color": MUTED},
    "ComboBox": {"background_color": SURFACE, "color": TEXT, "border_radius": 2},
    "ComboBox:disabled": {"background_color": BACKGROUND, "color": MUTED},
    "Separator": {"color": BORDER},
}
