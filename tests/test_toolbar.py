"""Rendered check of the Issues entry on Kit's main toolbar."""
import asyncio

from verify_kit import enable_extension, frames, ROOT


async def test_toolbar_click_opens_and_reuses_issues_panel():
    assert enable_extension('omni.kit.window.toolbar')
    assert enable_extension('omni.kit.ui_test')
    assert enable_extension('issues.tag')
    import omni.kit.widget.toolbar as toolbar_module
    from omni.kit.ui_test import Vec2, emulate_mouse_move_and_click
    from issues_tag.extension import get_runtime_service
    toolbar = toolbar_module.get_instance()
    assert get_runtime_service() is not None
    await frames(15)
    button = toolbar.get_widget('issues_open')
    assert button is not None and button.visible
    def center():
        return Vec2(float(button.screen_position_x) + float(button.computed_width) / 2,
                    float(button.screen_position_y) + float(button.computed_height) / 2)
    import omni.ui as ui
    await emulate_mouse_move_and_click(center())
    await frames(8)
    panel = ui.Workspace.get_window('Issues')
    assert panel is not None and panel.visible
    panel.visible = False
    await frames(5)
    await asyncio.sleep(.6)
    await emulate_mouse_move_and_click(center())
    await frames(8)
    assert ui.Workspace.get_window('Issues').visible
    assert toolbar.get_widget('issues_open') is button
    import omni.appwindow
    import omni.kit.app
    import omni.kit.renderer_capture
    renderer = omni.kit.renderer_capture.acquire_renderer_capture_interface()
    app_window = omni.appwindow.get_default_app_window()
    path = ROOT / 'verification/issues-toolbar.png'
    renderer.capture_next_frame_swapchain_to_file(str(path), app_window, {'format': 'png'})
    await omni.kit.app.get_app().next_update_async()
    renderer.wait_async_capture(app_window)
    for _ in range(60):
        if path.exists():
            break
        await omni.kit.app.get_app().next_update_async()
    assert path.exists(), 'Toolbar appearance screenshot was not delivered'
