"""A reviewer journey through the integrated native extension."""
from pxr import Gf, UsdGeom


async def test_full_review_workflow(service):
    from test_ui import controller_for, close_controller
    from issues_tag.elements import reference_for_prim, attachment_state
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
    extension = controller_for(service)
    await extension.select_issue(issue_id)
    extension._details.title.set_value('Door clearance')
    extension._details.description.set_value('Door clearance needs revision')
    await extension.save_details()
    related = UsdGeom.Cube.Define(service.stage, '/Other')
    related.AddTranslateOp().Set(Gf.Vec3d(5, 0, 0))
    await extension.select_issue(issue_id)
    service._context.get_selection().set_selected_prim_paths(['/Other'], False)
    await extension._details._action(extension._details.on_add_related)
    other = reference_for_prim(service.stage, '/Other')
    assert other in extension._session.record.related_elements
    assert other not in service.get_issue(issue_id).related_elements
    assert extension._session.record.anchor == anchor
    await extension._details._action(extension._details.on_remove_related, other)
    assert other not in extension._session.record.related_elements
    await extension._details._action(extension._details.on_add_related)
    await extension._details._action(extension._details.on_focus_related)
    service.viewport.restore(original)
    await extension._details._action(extension._details.on_capture_comment)
    await extension._details._action(extension._details.on_annotate_comment)
    extension._markup.core.add_element(20, 20, 70, 70, 'Arrow', {'Markup.Viewport.Arrow': {'color': 0xff0000ff, 'border_width': 5}, 'ArrowDirection': 1}, color=-16776961)
    extension._details.comment.set_value('Please check this opening')
    await extension._details._action(extension._details.on_add_comment)
    comment = extension._session.record.comments[-1]
    evidence = extension._session.comment_viewpoints[comment.id]
    assert not service.get_issue(issue_id).comments
    assert extension._session.viewpoint.id == original.id
    extension._session.update(status=Status.IN_PROGRESS)
    await extension._details._action(extension._details.on_save)
    assert other in service.get_issue(issue_id).related_elements
    assert service.store.get_viewpoint(evidence.id).snapshot.startswith(b'\x89PNG')
    # Existing saved comment annotation must copy before editing and preserve it on Discard.
    saved_record = service.get_issue(issue_id)
    await extension.select_issue(issue_id)
    await extension._details._action(extension._details.on_annotate_comment, comment.id)
    assert extension._session.comment_viewpoints[comment.id].id != evidence.id
    await extension.cancel_details('discard')
    assert service.get_issue(issue_id) == saved_record
    assert service.store.get_viewpoint(evidence.id) == evidence
    stage_path = ROOT / 'verification' / 'workflow-parent.usda'
    service.stage.GetRootLayer().Export(str(stage_path))
    await close_controller(extension)
    await service._context.open_stage_async(str(stage_path))
    await frames(20)
    service.author_name = 'Reviewer B'
    extension = controller_for(service)
    await extension.select_issue(issue_id)
    extension._details.comment.set_value('Reviewed after handoff')
    extension._session.update(status=Status.RESOLVED)
    await extension.save_details()
    record = service.get_issue(issue_id)
    assert record.author == 'Reviewer A'
    assert [c.author for c in record.comments] == ['Reviewer A', 'Reviewer B']
    assert record.initial_viewpoint_id == original.id
    assert service.store.get_viewpoint(evidence.id).snapshot.startswith(b'\x89PNG')
    cube = UsdGeom.Cube(service.stage.GetPrimAtPath('/Cube'))
    cube.GetSizeAttr().Set(4)
    assert attachment_state(service.stage, record.anchor) == 'needs_review'
    await extension.select_issue(issue_id)
    task = extension._details._action(extension._details.on_reattach)
    await frames(3)
    assert extension._window._placing and service.viewport.is_placing
    await service.viewport._place_at(service.viewport.viewport, (0, 0))
    await task
    assert attachment_state(service.stage, service.get_issue(issue_id).anchor) == 'needs_review'
    assert attachment_state(service.stage, extension._session.record.anchor) == 'verified'
    await extension._details._action(extension._details.on_save)
    assert attachment_state(service.stage, service.get_issue(issue_id).anchor) == 'verified'
    assert service.get_issue(issue_id).initial_viewpoint_id == original.id
    path = ROOT / 'verification' / 'workflow.bcf'
    write_bcf(export_document(service.store), path)
    document = read_bcf(path)
    await close_controller(extension)
    await service._context.new_stage_async()
    await frames(10)
    apply_import(plan_import(document, service.store), {}, service)
    imported = service.get_issue(issue_id)
    assert imported.status == Status.RESOLVED and len(imported.comments) == 2
    assert imported.anchor is None
    assert service.store.get_viewpoint(evidence.id).snapshot.startswith(b'\x89PNG')
