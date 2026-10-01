from verify_kit import enable_extension
from pathlib import Path

import omni.usd
from pxr import Sdf, Usd, UsdGeom
from verify_kit import ROOT, frames


async def service_for_new_scene():
    import omni.kit.app
    enable_extension("issues.tag", True)
    context = omni.usd.get_context()
    await context.new_stage_async()
    await frames(5)
    from issues_tag import get_runtime_service
    service = get_runtime_service()
    assert hasattr(service, "create_issue"), "Persistent issue actions are not implemented"
    return service


async def test_issue_comment_status_survive_reopen():
    service = await service_for_new_scene()
    from issues_tag.model import Status
    service.author_name = "First reviewer"
    issue_id = service.create_issue("Door overlaps wall", None, None)
    service.set_description(issue_id, "Door swing overlaps wall")
    comment_id = service.add_comment(issue_id, "Check clearance")
    for status in (Status.RESOLVED, Status.CLOSED, Status.OPEN):
        service.set_status(issue_id, status)
    path = ROOT / "verification" / "persistence.usda"
    service.stage.GetRootLayer().Export(str(path))
    opened, error = await omni.usd.get_context().open_stage_async(str(path))
    assert opened, f"Saved fixture could not reopen: {error}"
    await frames()
    record = service.get_issue(issue_id)
    assert record.id == issue_id
    assert record.description == "Door swing overlaps wall"
    assert record.status == Status.OPEN
    assert record.comments[0].id == comment_id
    assert record.comments[0].author == "First reviewer"
    assert record.comments[0].created_at.endswith("+00:00")


async def test_root_layer_ownership_and_read_only():
    service = await service_for_new_scene()
    source = Usd.Stage.CreateInMemory()
    UsdGeom.Cube.Define(source, "/Building")
    source.SetDefaultPrim(source.GetPrimAtPath("/Building"))
    source_path = ROOT / "verification" / "building.usda"
    source.GetRootLayer().Export(str(source_path))
    stage = service.stage
    prim = stage.DefinePrim("/Building", "Xform")
    prim.GetReferences().AddReference(str(source_path))
    source_layer = Sdf.Layer.FindOrOpen(str(source_path))
    before = source_layer.ExportToString()
    stage.SetEditTarget(stage.GetEditTargetForLocalLayer(stage.GetSessionLayer()))
    service.create_issue("Parent owns issue", None, None)
    assert stage.GetRootLayer().GetPrimAtPath("/Issues")
    assert not stage.GetSessionLayer().GetPrimAtPath("/Issues")
    assert source_layer.ExportToString() == before
    stage.GetRootLayer().SetPermissionToEdit(False)
    try:
        try:
            service.create_issue("Must reject", None, None)
        except ValueError:
            pass
        else:
            raise AssertionError("Read-only root accepted an issue")
    finally:
        stage.GetRootLayer().SetPermissionToEdit(True)


async def test_unsaved_state_and_next_reviewer():
    service = await service_for_new_scene()
    path = ROOT / "verification" / "handoff.usda"
    service.stage.GetRootLayer().Export(str(path))
    opened, error = await omni.usd.get_context().open_stage_async(str(path))
    assert opened, f"Handoff fixture could not open: {error}"
    await frames(5)
    assert service.stage, "Handoff stage disappeared after successful open"
    before = path.read_bytes()
    service.author_name = "Reviewer A"
    issue_id = service.create_issue("Check ceiling", None, None)
    assert service.is_dirty
    assert path.read_bytes() == before, "Issue edit auto-saved the scene"
    service.stage.GetRootLayer().Save()
    await omni.usd.get_context().close_stage_async()
    opened, error = await omni.usd.get_context().open_stage_async(str(path))
    assert opened, f"Handoff fixture could not reopen: {error}"
    await frames(5)
    service.author_name = "Reviewer B"
    service.add_comment(issue_id, "Reviewed the ceiling")
    record = service.get_issue(issue_id)
    assert record.author == "Reviewer A"
    assert record.comments[-1].author == "Reviewer B"


async def test_listeners_observe_complete_records():
    service = await service_for_new_scene()
    observed, errors = [], []
    def read_records():
        try:
            observed.append(service.list_issues())
        except ValueError as error:
            errors.append(str(error))
    service.add_listener(read_records)
    try:
        service.create_issue("Atomic review record")
        assert not errors, "Issue listeners saw a partial USD schema"
        assert observed and all(len(records) == 1 for records in observed), "Listeners saw partial records"
    finally:
        service.remove_listener(read_records)


async def test_issue_undo_preserves_unrelated_scene_edits():
    service = await service_for_new_scene()
    import omni.kit.undo
    issue_id = service.create_issue("Undoable review")
    service.stage.DefinePrim("/Unrelated", "Xform")
    service.set_description(issue_id, "Edited review")
    omni.kit.undo.undo()
    assert service.get_issue(issue_id).description == "Undoable review"
    assert service.stage.GetPrimAtPath("/Unrelated"), "Issue undo removed unrelated scene changes"
    omni.kit.undo.redo()
    assert service.get_issue(issue_id).description == "Edited review"


async def test_failed_issue_transaction_has_no_partial_records():
    service = await service_for_new_scene()
    from dataclasses import replace
    issue_id = service.create_issue("Original")
    original = service.get_issue(issue_id)
    def incomplete_import():
        service.store.put_issue(replace(original, description="Partial imported edit"))
        raise ValueError("Invalid imported viewpoint")
    try:
        service.mutate(incomplete_import)
    except ValueError:
        pass
    else:
        raise AssertionError("Failed transaction did not report failure")
    assert service.get_issue(issue_id) == original, "Failed import retained a partial issue edit"


async def test_viewpoint_lookup_does_not_walk_building_geometry():
    service = await service_for_new_scene()
    from uuid import uuid4
    from unittest.mock import patch
    from issues_tag.model import ViewpointRecord
    view = ViewpointRecord(str(uuid4()), snapshot=b"Saved evidence")
    service.create_issue("Review a large building", viewpoint=view)
    for index in range(128):
        UsdGeom.Cube.Define(service.stage, f"/Building/Component_{index}")
    visited_model_prims = []
    traverse = Usd.Stage.Traverse
    def measured_traversal(stage, *args, **kwargs):
        for prim in traverse(stage, *args, **kwargs):
            if str(prim.GetPath()).startswith("/Building"):
                visited_model_prims.append(str(prim.GetPath()))
            yield prim
    with patch.object(Usd.Stage, "Traverse", measured_traversal):
        assert service.store.get_viewpoint(view.id) == view
        try:
            service.store.get_viewpoint(str(uuid4()))
        except KeyError:
            pass
        else:
            raise AssertionError("Unknown viewpoint lookup did not report missing evidence")
    assert not visited_model_prims, "Saved viewpoint lookup traversed unrelated building geometry"
