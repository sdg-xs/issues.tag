"""Issue panel behavior tests against the active service and its real USD stage."""

import importlib.util

from issues_tag.model import Status


def require_panel():
    assert importlib.util.find_spec("issues_tag.window") is not None, "Issues panel is not implemented"


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


def test_panel_record_actions(service):
    require_panel()
    from issues_tag.window import IssuesWindow

    service.author_name = "First reviewer"
    window = IssuesWindow(service)
    try:
        issue_id = window.create_record("Door intersects the wall")
        assert window.selected_issue_id == issue_id
        assert service.get_issue(issue_id).description == "Door intersects the wall"
        window.submit_description("Door swing intersects the wall")
        window.submit_comment("Check the clearance against the revised plan")
        window.change_status(Status.RESOLVED)
        record = service.get_issue(issue_id)
        assert record.description == "Door swing intersects the wall"
        assert record.status == Status.RESOLVED
        assert record.comments[-1].text == "Check the clearance against the revised plan"
        assert record.comments[-1].author == "First reviewer"
        assert record.comments[-1].created_at
        window.change_status(Status.CLOSED)
        window.change_status(Status.OPEN)
        assert service.get_issue(issue_id).status == Status.OPEN
        assert service.is_dirty
    finally:
        window.destroy()


def test_panel_rejects_empty_input(service):
    require_panel()
    from issues_tag.window import IssuesWindow

    window = IssuesWindow(service)
    try:
        before = len(service.list_issues())
        try:
            window.create_record(" \n ")
        except ValueError:
            pass
        else:
            raise AssertionError("A blank description must fail")
        assert len(service.list_issues()) == before
        issue_id = window.create_record("Review the duct clearance")
        try:
            window.submit_comment("  ")
        except ValueError:
            pass
        else:
            raise AssertionError("A blank comment must fail")
        assert not service.get_issue(issue_id).comments
    finally:
        window.destroy()


def test_panel_rejects_unknown_selection(service):
    require_panel()
    from issues_tag.window import IssuesWindow

    window = IssuesWindow(service)
    try:
        issue_id = window.create_record("Review a reference")
        assert window.selected_issue_id == issue_id
        try:
            window.select_issue("not-an-issue")
        except (KeyError, ValueError):
            pass
        else:
            raise AssertionError("Selecting an unknown record must fail")
        assert service.get_issue(issue_id).description == "Review a reference"
    finally:
        window.destroy()


def test_panel_requires_selection_before_editing(service):
    require_panel()
    from issues_tag.window import IssuesWindow

    window = IssuesWindow(service)
    try:
        before = service.list_issues()
        for operation in (
            lambda: window.submit_description("Accidental edit"),
            lambda: window.submit_comment("Accidental comment"),
            lambda: window.change_status(Status.CLOSED),
        ):
            try:
                operation()
            except ValueError:
                pass
            else:
                raise AssertionError("Editing without a selected issue must fail")
        assert service.list_issues() == before
    finally:
        window.destroy()


def test_panel_reports_unsupported_scene_schema(service):
    require_panel()
    from pxr import Sdf
    from issues_tag.window import IssuesWindow

    prim = service.stage.DefinePrim("/Issues", "Scope")
    prim.CreateAttribute("issues:schemaVersion", Sdf.ValueTypeNames.Int, custom=True).Set(99)
    window = IssuesWindow(service)
    try:
        try:
            window.refresh()
        except ValueError as exc:
            raise AssertionError("Panel must display the scene load error instead of throwing") from exc
        assert "unsupported" in window.load_error.lower()
        assert service.stage.GetPrimAtPath("/Issues").GetAttribute("issues:schemaVersion").Get() == 99
    finally:
        window.destroy()


async def test_panel_stage_replacement_clears_drafts(service):
    require_panel()
    import omni.kit.app
    import omni.usd
    from issues_tag.model import ViewpointRecord
    from issues_tag.window import IssuesWindow

    window = IssuesWindow(service)
    try:
        window.create_record("Old scene issue")
        window.pending_viewpoint = ViewpointRecord("draft-evidence")
        window.comment.set_value("Old scene draft")
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()
        window.refresh()
        assert window.selected_issue_id is None
        assert window.pending_viewpoint is None
        assert window.comment.as_string == ""
        assert not service.list_issues()
    finally:
        window.destroy()


async def test_panel_comment_viewpoint_preserves_initial_view(service):
    require_panel()
    from issues_tag.window import IssuesWindow

    initial = service.viewport.capture()
    captured = service.viewport.capture()
    assert initial.id != captured.id
    issue_id = service.create_issue("Review the opening", viewpoint=initial)

    async def capture(selected_id):
        assert selected_id == issue_id
        return captured

    window = IssuesWindow(service, on_add_viewpoint=capture)
    try:
        window.select_issue(issue_id)
        await window._capture()
        window.submit_comment("Alternative review angle")
        record = service.get_issue(issue_id)
        assert record.initial_viewpoint_id == initial.id
        assert record.comments[-1].viewpoint_id == captured.id
        assert service.store.get_viewpoint(captured.id).camera == captured.camera
        assert window.pending_viewpoint is None
    finally:
        window.destroy()


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
    window = IssuesWindow(service)
    try:
        issue_id = window.create_record("Door swing intersects the adjacent wall")
        window.submit_comment("Confirm clear opening after the next model revision.")
        window.change_status(Status.IN_PROGRESS)
        service.create_issue("Duct route needs clearance above the doorway")
        service.create_issue("Verify corridor circulation width")
        window.select_issue(issue_id)
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
        window.destroy()
        viewport.setPosition(0, 0)
        viewport.width = 1100
