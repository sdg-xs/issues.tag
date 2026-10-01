"""Temporarily suppress viewport overlays without changing the application's UI."""
from contextlib import contextmanager


def overlapping_windows(viewport, windows):
    frame = viewport.get_frame('omni.kit.tool.markup')
    x, y = float(frame.screen_position_x), float(frame.screen_position_y)
    right, bottom = x + float(frame.computed_width), y + float(frame.computed_height)
    result = []
    for window in windows:
        if window == viewport or window.title == viewport.title or not window.visible or window.docked:
            continue
        ox, oy = float(window.position_x), float(window.position_y)
        if (ox < right and oy < bottom and ox + float(window.width) > x
                and oy + float(window.height) > y):
            result.append(window)
    return tuple(result)


@contextmanager
def clean_evidence_ui(layers, floating_windows, settings):
    visibility = [(item, item.visible) for item in (*layers, *floating_windows)]
    tool_key = '/persistent/exts/omni.kit.tool.markup/tool_hide'
    tool_hidden = settings.get(tool_key)
    try:
        settings.set(tool_key, True)
        for layer, _ in visibility:
            layer.visible = False
        yield
    finally:
        errors = []
        try:
            if tool_hidden is None:
                settings.destroy_item(tool_key)
            else:
                settings.set(tool_key, tool_hidden)
        except Exception as error:
            errors.append(error)
        for layer, visible in reversed(visibility):
            try:
                layer.visible = visible
            except ReferenceError:
                # A closed viewport has no UI state left to restore.
                pass
            except Exception as error:
                errors.append(error)
        if errors:
            raise ExceptionGroup('Evidence capture UI restoration failed', errors)
