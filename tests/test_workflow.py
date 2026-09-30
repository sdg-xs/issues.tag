"""A reviewer journey through the integrated native extension."""
from pathlib import Path
from pxr import Gf, UsdGeom


async def test_full_review_workflow(service):
    from issues_tag.window import IssuesWindow
    from issues_tag.elements import reference_for_prim, attachment_state, make_anchor
    from issues_tag.markup import MarkupAdapter
    from issues_tag.bcf import export_document, write_bcf, read_bcf, plan_import, apply_import
    from issues_tag.model import Status
    from omni.kit.viewport.utility import get_active_viewport
    from verify_kit import frames, ROOT
    camera = UsdGeom.Camera.Define(service.stage, '/WorkflowCamera')
    camera.AddTranslateOp().Set(Gf.Vec3d(0, 0, 10))
    cube = UsdGeom.Cube.Define(service.stage, '/Cube')
    viewport = get_active_viewport()
    viewport.camera_path = '/WorkflowCamera'
    await frames(30)
    service.author_name = 'Reviewer A'
    anchor = await service.viewport.pick(0, 0)
    assert anchor is not None
    original = service.viewport.capture()
    issue_id = service.create_issue('Check model clearance', anchor, original)
    panel = IssuesWindow(service)
    panel.select_issue(issue_id)
    panel.submit_description('Door clearance needs revision')
    related = UsdGeom.Cube.Define(service.stage, '/Other')
    service.set_related_elements(issue_id, (anchor.element, reference_for_prim(service.stage, '/Other')))
    adapter = MarkupAdapter(service)
    evidence = await adapter.capture_viewpoint()
    await adapter.begin(evidence)
    adapter.core.add_element(20, 20, 70, 70, 'Arrow', {'Markup.Viewport.Arrow': {'color': 0xff0000ff, 'border_width': 5}, 'ArrowDirection': 1}, color=-16776961)
    evidence = await adapter.finish(evidence)
    panel.pending_viewpoint = evidence
    panel.submit_comment('Please check this opening')
    panel.change_status(Status.IN_PROGRESS)
    stage_path = ROOT / 'verification' / 'workflow-parent.usda'
    service.stage.GetRootLayer().Export(str(stage_path))
    panel.destroy()
    await service._context.open_stage_async(str(stage_path))
    await frames(20)
    service.author_name = 'Reviewer B'
    panel = IssuesWindow(service)
    panel.select_issue(issue_id)
    panel.submit_comment('Reviewed after handoff')
    panel.change_status(Status.RESOLVED)
    record = service.get_issue(issue_id)
    assert record.author == 'Reviewer A'
    assert [c.author for c in record.comments] == ['Reviewer A', 'Reviewer B']
    assert record.initial_viewpoint_id == original.id
    assert service.store.get_viewpoint(evidence.id).snapshot.startswith(b'\x89PNG')
    cube = UsdGeom.Cube(service.stage.GetPrimAtPath('/Cube'))
    cube.GetSizeAttr().Set(4)
    assert attachment_state(service.stage, record.anchor) == 'needs_review'
    service.reattach(issue_id, make_anchor(service.stage, '/Cube', (0, 0, 2)))
    assert attachment_state(service.stage, service.get_issue(issue_id).anchor) == 'verified'
    assert service.get_issue(issue_id).initial_viewpoint_id == original.id
    path = ROOT / 'verification' / 'workflow.bcf'
    write_bcf(export_document(service.store), path)
    document = read_bcf(path)
    panel.destroy()
    adapter.destroy()
    await service._context.new_stage_async()
    await frames(10)
    apply_import(plan_import(document, service.store), {}, service)
    imported = service.get_issue(issue_id)
    assert imported.status == Status.RESOLVED and len(imported.comments) == 2
    assert imported.anchor is None
    assert service.store.get_viewpoint(evidence.id).snapshot.startswith(b'\x89PNG')
