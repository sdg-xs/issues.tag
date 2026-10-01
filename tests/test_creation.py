"""Lead-controlled rendered pin, native Markup, save and cancel workflow."""
import asyncio
from contextlib import contextmanager
from unittest.mock import patch

from pxr import Gf, Usd, UsdGeom, UsdLux
from verify_kit import frames, enable_extension


async def exercise_creation(service, save):
    from omni.kit.viewport.utility import get_active_viewport_window, next_viewport_frame_async
    assert enable_extension('omni.kit.ui_test')
    from omni.kit.ui_test import Vec2, emulate_mouse_move_and_click
    from test_ui import controller_for, close_controller
    window = get_active_viewport_window('Viewport')
    with Usd.EditContext(service.stage, service.stage.GetSessionLayer()):
        camera = UsdGeom.Camera.Define(service.stage, '/OmniverseKit_Persp')
        camera.MakeMatrixXform().Set(Gf.Matrix4d().SetTranslate(Gf.Vec3d(0, 0, 10)))
    UsdGeom.Cube.Define(service.stage, '/CreationCube')
    UsdLux.DistantLight.Define(service.stage, '/CreationLight').GetIntensityAttr().Set(3000)
    window.viewport_api.camera_path = '/OmniverseKit_Persp'
    window.focus()
    await frames(15)
    extension = controller_for(service)
    # Keep the floating review panel from covering the surface click.
    extension._window.window.visible = False
    window.focus()
    await frames(30)
    await asyncio.wait_for(next_viewport_frame_async(window.viewport_api, 1), 15)
    assert (await service.viewport.pick(0, 0)).element.prim_path == '/CreationCube'
    prior = service.list_issues()
    occluders = []
    async def edit_draft():
        assert service.list_issues() == prior, 'Draft appeared in the saved issue list'
        assert extension._markup.core.editing_markup is not None, 'Markup did not open after pin placement'
        assert str(window.viewport_api.camera_path) == '/OmniverseKit_Persp'
        assert not any(p.GetName().startswith('IssuesReviewCamera_') for p in service.stage.Traverse())
        await frames(5)
        if save:
            extension._markup.core.add_element(20, 20, 70, 70, 'Arrow',
                {'Markup.Viewport.Arrow': {'color': 0xff0000ff, 'border_width': 5}, 'ArrowDirection': 1}, color=-16776961)
            import omni.ui as ui
            occluder = ui.Window('Screenshot occlusion probe', width=150, height=130)
            with occluder.frame:
                ui.Rectangle(style={'background_color': 0xffff00ff})
            drawing = window.get_frame('omni.kit.tool.markup')
            occluder.position_x = float(drawing.screen_position_x) + float(drawing.computed_width) * .4
            occluder.position_y = float(drawing.screen_position_y) + float(drawing.computed_height) * .4
            occluders.append(occluder)
            await frames(5)
            extension._details.title.set_value('Clearance')
            extension._details.description.set_value('Pin with saved Markup evidence')
            return await extension.save_details()
        else:
            await extension.cancel_details('discard')
            return None
    task = None
    from issues_tag import evidence_capture
    clean_ui = evidence_capture.clean_evidence_ui
    capture_count = 0
    @contextmanager
    def checked_capture(overlays, floating_windows, settings):
        nonlocal capture_count
        import carb.settings
        settings = carb.settings.get_settings()
        hide_ui = settings.get('/app/window/hideUi')
        tabs = window.dock_tab_bar_enabled
        original = [layer.visible for layer in overlays]
        with clean_ui(overlays, floating_windows, settings):
            assert overlays and not any(layer.visible for layer in overlays)
            assert not any(other.visible for other in floating_windows)
            if occluders:
                assert any(other.title == 'Screenshot occlusion probe' for other in floating_windows)
            assert settings.get('/app/window/hideUi') == hide_ui
            assert window.dock_tab_bar_enabled == tabs
            assert window.get_frame('omni.kit.tool.markup').visible
            assert window.viewport_widget.visible
            capture_count += 1
            yield
        assert [layer.visible for layer in overlays] == original
        assert all(other.visible for other in occluders)
    try:
        with patch('issues_tag.evidence_capture.clean_evidence_ui', checked_capture):
            task = asyncio.create_task(extension.begin_creation())
            await frames(5)
            assert service.viewport.is_placing
            await asyncio.sleep(.6)
            frame = window.frame
            center = Vec2(float(frame.screen_position_x) + float(frame.computed_width) / 2,
                          float(frame.screen_position_y) + float(frame.computed_height) / 2)
            await emulate_mouse_move_and_click(center)
            await asyncio.wait_for(task, 60)
            issue_id = await edit_draft()
        if save:
            issue = service.get_issue(issue_id)
            assert issue.description == 'Pin with saved Markup evidence'
            assert issue.anchor is not None
            evidence = service.store.get_viewpoint(issue.initial_viewpoint_id)
            assert evidence.snapshot.startswith(b'\x89PNG') and evidence.markup_path
            from PIL import Image
            import io
            pixels = list(Image.open(io.BytesIO(evidence.snapshot)).convert('RGB').getdata())
            assert not any(r > 240 and b > 240 and g < 20 for r, g, b in pixels), 'Overlapping UI leaked into snapshot'
            assert any(r > 240 and g < 30 and b < 30 for r, g, b in pixels), 'Markup arrow disappeared'
            assert capture_count == 2, 'Initial and annotated snapshots must both hide overlays'
            service.open_issue(issue_id)
            assert str(window.viewport_api.camera_path) == '/OmniverseKit_Persp'
            from verify_kit import ROOT
            (ROOT / 'verification' / 'clean-evidence.png').write_bytes(evidence.snapshot)
            from issues_tag.store import IssueStore
            from issues_tag.bcf import export_document, write_bcf, read_bcf
            saved_path = ROOT / 'verification' / 'pin-markup-parent.usda'
            service.stage.GetRootLayer().Export(str(saved_path))
            saved = IssueStore(Usd.Stage.Open(str(saved_path)))
            assert saved.get_issue(issue_id).description == issue.description
            assert saved.get_viewpoint(evidence.id).snapshot == evidence.snapshot
            bcf_path = ROOT / 'verification' / 'pin-markup.bcf'
            write_bcf(export_document(saved), bcf_path)
            exchanged = read_bcf(bcf_path)
            assert any(view.snapshot == evidence.snapshot for view in exchanged.viewpoints)
        else:
            assert issue_id is None and service.list_issues() == prior
            root = service.stage.GetPrimAtPath('/Viewport_Markups')
            assert not root or not root.GetChildren(), 'Cancel left native draft evidence'
        assert not extension._dialogs
        assert extension._markup.core.current_markup is None
        assert extension._markup.core.editing_markup is None
    finally:
        for occluder in occluders:
            occluder.destroy()
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        await close_controller(extension)


async def test_pin_opens_markup_and_saves_annotated_initial_view(service):
    await exercise_creation(service, save=True)


async def test_cancel_pin_markup_draft_leaves_no_issue(service):
    await exercise_creation(service, save=False)
