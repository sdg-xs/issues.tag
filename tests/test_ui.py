"""Separate issue panels, staged edits, and import preview on a real Kit stage."""
import importlib.util
from issues_tag.model import Status


def require_panel():
    assert importlib.util.find_spec('issues_tag.window') is not None


def controller_for(service):
    from issues_tag.extension import IssuesController
    from issues_tag.markup import MarkupAdapter
    extension = IssuesController()
    extension._service, extension._viewport = service, service.viewport
    extension._markup, extension._window = MarkupAdapter(service), None
    extension._markup.suppress_window_close = extension._evidence_ui
    service.native_view_recaller = extension._markup.restore_viewpoint
    extension._session = extension._details = extension._annotation = extension._edit_task = None
    extension._owned_views, extension._tasks, extension._dialogs, extension._menus = {}, set(), [], []
    extension._shutting_down, extension._toolbar = False, None
    extension.show()
    return extension


async def close_controller(extension):
    if extension._session:
        await extension.cancel_details('discard')
    for task in tuple(extension._tasks):
        task.cancel()
    if extension._tasks:
        import asyncio
        await asyncio.gather(*extension._tasks, return_exceptions=True)
    extension._window.destroy()
    extension._markup.destroy()
    extension._viewport.on_pin_clicked = None
    service = extension._service
    service.native_view_recaller = None


async def test_panel_placement_cancel_does_not_create_issue(service):
    from verify_kit import frames
    extension = controller_for(service)
    before = service.list_issues()
    try:
        extension._window._create()
        await frames(3)
        assert extension._window._placing and service.viewport.is_placing
        extension._window._create()
        assert len(extension._tasks) == 1
        extension._window._cancel_placement()
        await frames(3)
        assert not extension._window._placing and not service.viewport.is_placing
        assert service.list_issues() == before
    finally:
        await close_controller(extension)


async def test_panel_attachment_validation_ignores_camera_navigation(service):
    from pxr import Sdf, UsdGeom
    from issues_tag.elements import make_anchor, attachment_state
    from verify_kit import frames
    cube = UsdGeom.Cube.Define(service.stage, '/Model/Element')
    cube.GetPrim().CreateAttribute('ifc:GlobalId', Sdf.ValueTypeNames.String, custom=True).Set('panel-stable-element')
    anchor = make_anchor(service.stage, str(cube.GetPath()), (0, 0, 0))
    issue_id = service.create_issue('Review attachment', anchor=anchor)
    camera = UsdGeom.Camera.Define(service.stage, '/ReviewCamera')
    translation = camera.AddTranslateOp()
    extension = controller_for(service)
    try:
        await extension.select_issue(issue_id)
        await frames(3)
        revision = service.viewport.scene_revision
        for offset in range(4):
            translation.Set((offset, 2, 8))
            await frames(1)
        assert service.viewport.scene_revision == revision
        assert extension._session.record.anchor == anchor
        duplicate = UsdGeom.Cube.Define(service.stage, '/Model/Duplicate')
        duplicate.GetPrim().CreateAttribute('ifc:GlobalId', Sdf.ValueTypeNames.String, custom=True).Set('panel-stable-element')
        await frames(3)
        assert attachment_state(service.stage, anchor) == 'ambiguous'
        service.stage.RemovePrim(str(duplicate.GetPath()))
        cube.GetSizeAttr().Set(3)
        await frames(3)
        assert attachment_state(service.stage, anchor) == 'needs_review'
    finally:
        await close_controller(extension)


def test_import_preview_requires_explicit_apply(service):
    assert importlib.util.find_spec("issues_tag.import_window") is not None, "BCF conflict preview is not implemented"
    from dataclasses import replace
    from issues_tag.bcf import BcfDocument, apply_import, plan_import
    from issues_tag.import_window import ImportWindow

    issue_id = service.create_issue("Local review description")
    local = service.get_issue(issue_id)
    incoming = replace(local, description="Imported review description", status=Status.RESOLVED)
    plan = plan_import(BcfDocument(issues=(incoming,), viewpoints=()), service.store)
    assert plan.conflicts, "The preview fixture must contain conflicting edits"
    panel = ImportWindow(plan, lambda choices: apply_import(plan, choices, service))
    try:
        assert service.get_issue(issue_id).description == "Local review description"
        for conflict in plan.conflicts:
            assert panel.choices[conflict.key] == "keep_local"
            panel.set_choice(conflict.key, "use_imported")
        panel.apply_choices()
        assert service.get_issue(issue_id).description == "Imported review description"
        assert service.get_issue(issue_id).status == Status.RESOLVED
    finally:
        panel.destroy()


async def test_panel_record_actions(service):
    service.author_name = 'First reviewer'
    issue_id = service.create_issue('Door intersects the wall')
    original = service.get_issue(issue_id)
    extension = controller_for(service)
    try:
        await extension.select_issue(issue_id)
        extension._details.title.set_value('Door clearance')
        extension._details.description.set_value('Door swing intersects the wall')
        extension._details.comment.set_value('Check the clearance against the revised plan')
        extension._session.update(status=Status.RESOLVED)
        assert service.get_issue(issue_id) == original
        assert await extension.save_details() == issue_id
        record = service.get_issue(issue_id)
        assert record.title == 'Door clearance'
        assert record.description == 'Door swing intersects the wall'
        assert record.status == Status.RESOLVED
        assert record.comments[-1].author == 'First reviewer'
        assert record.comments[-1].created_at
        for status in (Status.CLOSED, Status.OPEN):
            await extension.select_issue(issue_id)
            extension._session.update(status=status)
            assert await extension.save_details() == issue_id
        assert service.get_issue(issue_id).status == Status.OPEN
        assert service.is_dirty
    finally:
        await close_controller(extension)


async def test_panel_rejects_empty_input(service):
    issue_id = service.create_issue('Review duct clearance')
    before = service.get_issue(issue_id)
    extension = controller_for(service)
    try:
        await extension.select_issue(issue_id)
        extension._details.title.set_value('  ')
        assert await extension.save_details() is None
        assert extension._details._error
        assert service.get_issue(issue_id) == before
        extension._details.title.set_value('Duct clearance')
        extension._details.comment.set_value('  ')
        assert await extension.save_details() == issue_id
        assert not service.get_issue(issue_id).comments
    finally:
        await close_controller(extension)


async def test_panel_rejects_unknown_selection(service):
    issue_id = service.create_issue('Review a reference')
    extension = controller_for(service)
    try:
        assert await extension.select_issue('not-an-issue') is None
        assert extension._window._error
        assert extension._session is None
        assert service.get_issue(issue_id).description == 'Review a reference'
    finally:
        await close_controller(extension)


async def test_panel_requires_selection_before_editing(service):
    extension = controller_for(service)
    before = service.list_issues()
    try:
        assert await extension.save_details() is None
        assert await extension.replace_screenshot() is None
        assert await extension.annotate_details() is None
        assert service.list_issues() == before
    finally:
        await close_controller(extension)


def test_panel_reports_unsupported_scene_schema(service):
    from pxr import Sdf
    from issues_tag.window import IssuesWindow
    prim = service.stage.DefinePrim('/Issues', 'Scope')
    prim.CreateAttribute('issues:schemaVersion', Sdf.ValueTypeNames.Int, custom=True).Set(99)
    window = IssuesWindow(service, on_select=lambda value: None, on_create=lambda: None)
    try:
        window.refresh()
        assert 'unsupported' in window.load_error.lower()
        assert prim.GetAttribute('issues:schemaVersion').Get() == 99
    finally:
        window.destroy()


async def test_panel_stage_replacement_rejects_stale_draft(service):
    from verify_kit import frames
    issue_id = service.create_issue('Old scene issue')
    extension = controller_for(service)
    try:
        await extension.select_issue(issue_id)
        extension._details.comment.set_value('Old scene draft')
        draft = extension._session
        await service._context.new_stage_async()
        await frames(3)
        extension._window.refresh()
        assert extension._window.selected_issue_id is None
        assert await extension.save_details() is None
        assert extension._session is draft and extension._details._error
        assert not service.list_issues()
    finally:
        await close_controller(extension)


async def test_panel_comment_viewpoint_preserves_initial_view(service):
    from unittest.mock import patch
    initial, captured = service.viewport.capture(), service.viewport.capture()
    issue_id = service.create_issue('Review the opening', viewpoint=initial)
    extension = controller_for(service)
    async def capture():
        return captured
    try:
        await extension.select_issue(issue_id)
        with patch.object(extension._markup, 'capture_viewpoint', capture):
            await extension._details._action(extension._details.on_capture_comment)
        extension._details.comment.set_value('Alternative review angle')
        await extension._details._action(extension._details.on_add_comment)
        assert not service.get_issue(issue_id).comments
        await extension._details._action(extension._details.on_comment_view, captured.id)
        extension._details.comment.set_value('Metadata only follow-up')
        assert await extension._details._action(extension._details.on_save) == issue_id
        record = service.get_issue(issue_id)
        assert record.initial_viewpoint_id == initial.id
        assert record.comments[0].viewpoint_id == captured.id
        assert record.comments[1].text == 'Metadata only follow-up'
        assert service.store.get_viewpoint(captured.id).camera == captured.camera
    finally:
        await close_controller(extension)


async def preview_panel(service):
    """Visible-only native UI evidence, dispatched separately from headless tests."""
    require_panel()
    from pathlib import Path

    import omni.kit.app
    import omni.appwindow
    import omni.kit.renderer_capture
    from omni.kit.viewport.utility import get_active_viewport_window
    from pxr import Gf, UsdGeom, UsdLux

    from issues_tag.window import IssuesWindow

    stage = service.stage
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1)
    for name, position, scale, color in (
        ("Floor", (0, 0, 0), (9, .2, 7), (.22, .28, .31)),
        ("WallLeft", (-2.8, 2, 0), (3, 4, .3), (.64, .68, .69)),
        ("WallRight", (2.8, 2, 0), (3, 4, .3), (.64, .68, .69)),
        ("Lintel", (0, 3.7, 0), (2.6, .6, .3), (.64, .68, .69)),
        ("Door", (.8, 1.5, .5), (.15, 3, 1.7), (.17, .67, .59)),
        ("Duct", (0, 3.3, 1.3), (6, .5, .6), (.39, .46, .49)),
    ):
        cube = UsdGeom.Cube.Define(stage, f"/Building/{name}")
        cube.GetSizeAttr().Set(1)
        cube.AddTranslateOp().Set(position)
        cube.AddScaleOp().Set(scale)
        cube.GetDisplayColorAttr().Set([color])
    light = UsdLux.DomeLight.Define(stage, "/PreviewLight")
    light.GetIntensityAttr().Set(1000)
    camera = UsdGeom.Camera.Define(stage, "/PreviewCamera")
    camera.GetFocalLengthAttr().Set(35)
    camera.GetClippingRangeAttr().Set((.01, 1000))
    camera.AddTransformOp().Set(Gf.Matrix4d().SetLookAt(Gf.Vec3d(10, 8, 13), Gf.Vec3d(0, 1.8, 0), Gf.Vec3d(0, 1, 0)).GetInverse())
    viewport = get_active_viewport_window('Viewport')
    viewport.viewport_api.camera_path = camera.GetPath()
    assert viewport is not None, "Preview needs a native rendered viewport"
    service.author_name = "Model reviewer"
    extension = controller_for(service)
    window = extension._window
    try:
        issue_id = service.create_issue("Door swing intersects the adjacent wall")
        await extension.select_issue(issue_id)
        extension._details.comment.set_value("Confirm clear opening after the next model revision.")
        extension._session.update(status=Status.IN_PROGRESS)
        await extension.save_details()
        service.create_issue("Duct route needs clearance above the doorway")
        service.create_issue("Verify corridor circulation width")
        await extension.select_issue(issue_id)
        viewport.setPosition(0, 0)
        viewport.width = 680
        viewport.height = 800
        window.window.setPosition(680, 0)
        window.window.width = 420
        window.window.height = 800
        window.show()
        app = omni.kit.app.get_app()
        for _ in range(45):
            await app.next_update_async()
        path = Path(__file__).resolve().parent.parent / "verification" / "issues-panel.png"
        path.parent.mkdir(exist_ok=True)
        if path.exists():
            path.unlink()
        renderer = omni.kit.renderer_capture.acquire_renderer_capture_interface()
        app_window = omni.appwindow.get_default_app_window()
        assert app_window is not None, "Visible preview requires a default application window"
        renderer.capture_next_frame_swapchain_to_file(str(path), app_window, {"format": "png"})
        await app.next_update_async()
        renderer.wait_async_capture(app_window)
        for _ in range(60):
            if path.exists():
                break
            await app.next_update_async()
        assert path.exists(), "Native panel screenshot was not captured"
        assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"), "Panel capture must be a PNG"
        assert window.window.width >= 380, "Preview panel must meet the minimum usable width"
    finally:
        await close_controller(extension)
        viewport.setPosition(0, 0)
        viewport.width = 1100


async def preview_placement_prompt(service):
    """Capture the real armed placement guidance and native Cancel action."""
    require_panel()
    from pathlib import Path
    import omni.appwindow
    import omni.kit.app
    import omni.kit.renderer_capture
    from omni.kit.viewport.utility import get_active_viewport_window
    from pxr import Gf, UsdGeom, UsdLux
    from issues_tag.window import IssuesWindow

    stage = service.stage
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    cube = UsdGeom.Cube.Define(stage, "/PlacementTarget")
    cube.GetSizeAttr().Set(3)
    cube.GetDisplayColorAttr().Set([(.3, .55, .5)])
    light = UsdLux.DomeLight.Define(stage, "/PlacementLight")
    light.GetIntensityAttr().Set(1000)
    camera = UsdGeom.Camera.Define(stage, "/PlacementCamera")
    camera.AddTransformOp().Set(Gf.Matrix4d().SetLookAt(Gf.Vec3d(6, 5, 8), Gf.Vec3d(0, 0, 0), Gf.Vec3d(0, 1, 0)).GetInverse())
    viewport = get_active_viewport_window("Viewport")
    assert viewport is not None, "Placement preview requires the native review viewport"
    viewport.viewport_api.camera_path = camera.GetPath()
    viewport.width = 680
    viewport.height = 800

    extension = controller_for(service)
    window = extension._window
    window.window.setPosition(680, 0)
    window.window.height = 800
    app = omni.kit.app.get_app()
    try:
        before = service.list_issues()
        window._create()
        for _ in range(15):
            await app.next_update_async()
        assert service.viewport.is_placing and window._placing
        path = Path(__file__).resolve().parent.parent / "verification" / "issues-placement.png"
        path.parent.mkdir(exist_ok=True)
        if path.exists():
            path.unlink()
        renderer = omni.kit.renderer_capture.acquire_renderer_capture_interface()
        app_window = omni.appwindow.get_default_app_window()
        renderer.capture_next_frame_swapchain_to_file(str(path), app_window, {"format": "png"})
        await app.next_update_async()
        renderer.wait_async_capture(app_window)
        for _ in range(60):
            if path.exists():
                break
            await app.next_update_async()
        assert path.exists() and path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        window._cancel_placement()
        await app.next_update_async()
        assert not window._placing
        assert service.list_issues() == before
    finally:
        window._cancel_placement()
        await close_controller(extension)
        viewport.width = 1100
