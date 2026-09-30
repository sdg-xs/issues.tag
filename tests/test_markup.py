import asyncio
import importlib.util
import io
from pathlib import Path
from pxr import Gf, UsdGeom


def adapter_for(service):
    assert importlib.util.find_spec('issues_tag.markup'), 'Editable Markup evidence is not implemented'
    from issues_tag.markup import MarkupAdapter
    return MarkupAdapter(service)


async def test_evidence_rejects_secondary_viewport_before_mutation(service):
    from issues_tag.viewport import ViewportAdapter
    from omni.kit.viewport.utility import create_viewport_window
    from verify_kit import frames
    camera = UsdGeom.Camera.Define(service.stage, '/SecondaryEvidenceCamera')
    camera.AddTranslateOp().Set(Gf.Vec3d(20, 0, 10))
    window = create_viewport_window('Secondary evidence test', width=320, height=240,
                                    camera_path='/SecondaryEvidenceCamera')
    adapter = adapter_for(service)
    original = service.viewport
    service.viewport = ViewportAdapter(service, window.viewport_api)
    await frames(10)
    before = service.stage.GetRootLayer().ExportToString()
    try:
        try:
            await adapter.capture_viewpoint()
        except ValueError as error:
            assert 'primary Viewport' in str(error)
        else:
            raise AssertionError('Secondary camera received evidence from the primary viewport')
        assert service.stage.GetRootLayer().ExportToString() == before, 'Rejected capture authored evidence'
    finally:
        adapter.destroy()
        service.viewport = original
        window.destroy()


async def test_initial_view_can_start_markup(service):
    adapter = adapter_for(service)
    assert callable(getattr(adapter, 'ensure_editable', None)), 'Initial review views cannot start editable Markup'
    original = service.viewport.capture()
    ready = await adapter.ensure_editable(original)
    assert ready.id == original.id and ready.camera == original.camera
    assert ready.markup_path
    await adapter.begin(ready)
    await adapter.finish(ready, save=False)
    adapter.destroy()


async def test_annotation_rejects_overlapping_ownership(service):
    adapter = adapter_for(service)
    first = await adapter.capture_viewpoint()
    second = await adapter.capture_viewpoint()
    await adapter.begin(first)
    try:
        await adapter.begin(second)
    except ValueError:
        pass
    else:
        adapter.destroy()
        raise AssertionError('A second annotation replaced the active viewpoint owner')
    await adapter.finish(first, save=False)
    adapter.destroy()


async def test_annotation_releases_navigation(service):
    adapter = adapter_for(service)
    record = await adapter.capture_viewpoint()
    await adapter.begin(record)
    await adapter.finish(record, save=True)
    assert adapter.core.current_markup is None, 'Finished annotation retains active Markup navigation state'
    adapter.destroy()


async def test_failed_annotation_begin_releases_vendor_edit(service):
    from dataclasses import replace
    adapter = adapter_for(service)
    record = await adapter.capture_viewpoint()
    target = service.stage.GetEditTarget()
    try:
        try:
            await adapter.begin(replace(record, camera={}))
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid saved camera started an annotation')
        assert adapter.core.current_markup is None, 'Failed restore left NVIDIA Markup editing active'
        assert service.stage.GetEditTarget() == target
        await adapter.begin(record)
        await adapter.finish(record, save=False)
    finally:
        adapter.destroy()


async def test_stale_annotation_releases_owner_without_touching_new_scene(service):
    from verify_kit import frames
    old = adapter_for(service)
    record = await old.capture_viewpoint()
    await old.begin(record)
    await service._context.new_stage_async()
    await frames(10)
    current = adapter_for(service)
    try:
        fresh = await current.capture_viewpoint()
        await current.begin(fresh)
        owner = current.core.current_markup
        try:
            await old.finish(record, save=False)
        except ValueError:
            pass
        else:
            raise AssertionError('Old annotation was accepted in a replacement scene')
        assert current.core.current_markup == owner, 'Stale cleanup cleared the new scene annotation'
        await current.finish(fresh, save=False)
        resumed = await old.capture_viewpoint()
        assert resumed.markup_path, 'Stage invalidation permanently blocked the old adapter'
        await current.begin(fresh)
        owner = current.core.current_markup
        old.destroy()
        assert current.core.current_markup == owner, 'Destroying stale adapter cleared another annotation'
        await current.finish(fresh, save=False)
    finally:
        old.destroy()
        current.destroy()


async def test_annotated_comment_reopens_editably(service):
    adapter = adapter_for(service)
    from issues_tag.viewport import ViewportAdapter
    from omni.kit.viewport.utility import get_active_viewport
    from verify_kit import frames
    from PIL import Image
    from pxr import UsdLux
    camera = UsdGeom.Camera.Define(service.stage, '/Camera')
    camera.AddTranslateOp().Set(Gf.Vec3d(0, 0, 10))
    UsdGeom.Cube.Define(service.stage, '/Cube')
    UsdLux.DomeLight.Define(service.stage, '/EvidenceLight').GetIntensityAttr().Set(1000)
    viewport = get_active_viewport()
    viewport.camera_path = '/Camera'
    service.viewport = ViewportAdapter(service, viewport)
    await frames(30)
    initial = service.viewport.capture()
    issue = service.create_issue('Markup evidence', viewpoint=initial)
    record = await adapter.capture_viewpoint()
    before = record.snapshot
    await adapter.begin(record)
    adapter.core.add_element(20, 20, 70, 60, 'Arrow', {'Markup.Viewport.Arrow': {'color': 0xff0000ff, 'border_width': 5}, 'ArrowDirection': 1}, color=-16776961)
    adapter.core.add_element(30, 60, 70, 80, 'Label', {'Markup.Viewport.Comment': {'color': 0xff0000ff, 'font_size': 24}}, text='Check opening', color=-16776961, pixel_size=(350, 90))
    annotated = await adapter.finish(record)
    (Path(__file__).resolve().parent.parent / 'verification' / 'markup-before.png').write_bytes(before)
    (Path(__file__).resolve().parent.parent / 'verification' / 'markup-after.png').write_bytes(annotated.snapshot)
    assert annotated.snapshot.startswith(b'\x89PNG')
    assert annotated.snapshot != before, 'Annotated image must include the drawn evidence'
    rendered = Image.open(io.BytesIO(annotated.snapshot)).convert('RGB')
    upper = rendered.crop((0, 0, rendered.width, rendered.height // 2))
    assert sum(r > 180 and g < 100 and b < 100 for r, g, b in upper.getdata()) > 10, 'The rendered evidence has no red annotation in the model area'
    Image.open(io.BytesIO(annotated.snapshot)).verify()
    service.add_comment(issue, 'Review arrow', annotated)
    assert service.get_issue(issue).initial_viewpoint_id == initial.id
    root = Path(__file__).resolve().parent.parent / 'verification' / 'markup-parent.usda'
    service.stage.GetRootLayer().Export(str(root))
    await service._context.open_stage_async(str(root))
    await frames(20)
    saved = service.store.get_viewpoint(record.id)
    assert service.stage.GetRootLayer().GetPrimAtPath(saved.markup_path)
    await adapter.begin(saved)
    assert len(adapter.core.get_markup_elements()) >= 2
    await adapter.finish(saved, save=False)
    adapter.destroy()


async def test_capture_stage_change_discards_result(service):
    adapter = adapter_for(service)
    task = asyncio.ensure_future(adapter.capture_viewpoint())
    await asyncio.sleep(0)
    await service._context.new_stage_async()
    try:
        await task
    except (ValueError, asyncio.CancelledError):
        pass
    else:
        raise AssertionError('Capture survived a stage replacement')
    assert not service.list_issues()
    adapter.destroy()


async def test_capture_preserves_replacement_vendor_owner(service):
    adapter = adapter_for(service)
    existing = await adapter.capture_viewpoint()
    from omni.kit.markup.core import MarkupChangeCallbacks
    replacement = adapter.core.get_markup_from_prim_path(existing.markup_path)
    recalled = []
    def replace_owner(*args):
        recalled.append(True)
        adapter.core.recall_markup(replacement, without_camera=True, force=True)
    callback = MarkupChangeCallbacks(on_markup_created=replace_owner)
    adapter.core.register_callback(callback)
    try:
        try:
            await adapter.capture_viewpoint()
        except ValueError:
            pass
        else:
            raise AssertionError('Capture accepted evidence after NVIDIA Markup owner changed')
        assert recalled, 'Replacement must occur during the real creation callback'
        assert adapter.core.current_markup == replacement, 'Capture cleanup cleared the replacement owner'
    finally:
        adapter.core.deregister_callback(callback)
        editing = adapter.core.editing_markup
        if editing:
            adapter.core.end_edit_markup(editing, save=True, update_thumbnail=False)
        adapter.core.recall_markup(None)
        adapter.core.unlock_camera()
        adapter.destroy()


async def test_finish_preserves_replacement_vendor_owner(service):
    adapter = adapter_for(service)
    other = adapter_for(service)
    first = await adapter.capture_viewpoint()
    second = await adapter.capture_viewpoint()
    original_target = service.stage.GetSessionLayer()
    service.stage.SetEditTarget(original_target)
    try:
        await adapter.begin(first)
        await other.begin(second)
        owner = other.core.current_markup
        try:
            await adapter.finish(first)
        except ValueError:
            pass
        else:
            raise AssertionError('Apply captured evidence belonging to another vendor owner')
        assert other.core.current_markup == owner
        await other.finish(second, save=False)
        assert service.stage.GetEditTarget().GetLayer() == original_target, 'Ownership handoff lost the original USD edit target'
    finally:
        adapter.destroy()
        other.destroy()


async def test_capture_camera_matches_view_after_markup_activation(service):
    from omni.kit.viewport.utility import get_active_viewport_window
    window = get_active_viewport_window('Viewport')
    camera = UsdGeom.Camera.Define(service.stage, '/CaptureActivationCamera')
    position = camera.AddTranslateOp()
    position.Set(Gf.Vec3d(0, 0, 10))
    window.viewport_api.camera_path = camera.GetPath()
    adapter = adapter_for(service)
    try:
        task = asyncio.ensure_future(adapter.capture_viewpoint())
        await asyncio.sleep(0)
        position.Set(Gf.Vec3d(3, 4, 12))
        record = await task
        assert record.camera['transform'][12:15] == [3, 4, 12], 'Saved camera predates the view used for Markup creation'
    finally:
        adapter.destroy()


async def test_creation_callback_cancellation_releases_markup_and_edit_target(service):
    adapter = adapter_for(service)
    await adapter._ready()
    from omni.kit.markup.core import MarkupChangeCallbacks
    original_target = service.stage.GetSessionLayer()
    service.stage.SetEditTarget(original_target)
    task = None
    def cancel_capture(*args):
        task.cancel()
    callback = MarkupChangeCallbacks(on_markup_created=cancel_capture)
    adapter.core.register_callback(callback)
    try:
        task = asyncio.ensure_future(adapter.capture_viewpoint())
        try:
            await task
        except asyncio.CancelledError:
            pass
        else:
            raise AssertionError('The real creation callback did not cancel capture')
        assert adapter.core.current_markup is None, 'Cancelled creation retains Markup navigation ownership'
        assert adapter.core.editing_markup is None, 'Cancelled creation leaves vendor editing active'
        assert service.stage.GetEditTarget().GetLayer() == original_target
    finally:
        adapter.core.deregister_callback(callback)
        editing = adapter.core.editing_markup
        if editing:
            adapter.core.end_edit_markup(editing, save=True, update_thumbnail=False)
        adapter.core.recall_markup(None)
        adapter.core.unlock_camera()
        service.stage.SetEditTarget(original_target)
        adapter.destroy()


async def test_external_vendor_edit_defers_original_target_restoration(service):
    from verify_kit import frames
    adapter = adapter_for(service)
    first = await adapter.capture_viewpoint()
    second = await adapter.capture_viewpoint()
    original_target = service.stage.GetSessionLayer()
    service.stage.SetEditTarget(original_target)
    core = adapter.core
    try:
        await adapter.begin(first)
        external = core.get_markup_from_prim_path(second.markup_path)
        core.recall_markup(external, without_camera=True, force=True)
        assert core.begin_edit_markup(external)
        try:
            await adapter.finish(first)
        except ValueError:
            pass
        else:
            raise AssertionError('Apply accepted an externally replaced annotation')
        assert service.stage.GetEditTarget().GetLayer() == service.stage.GetRootLayer(), 'Active external drawing was redirected into the original layer'
        assert core.current_markup == external
        core.end_edit_markup(external, save=True, update_thumbnail=False)
        await frames(4)
        assert service.stage.GetEditTarget().GetLayer() == original_target, 'Original target was forgotten after the external edit ended'
        assert core.current_markup == external, 'Deferred target restoration cleared the external review'
    finally:
        editing = core.editing_markup
        if editing:
            core.end_edit_markup(editing, save=True, update_thumbnail=False)
        core.recall_markup(None)
        core.unlock_camera()
        adapter.destroy()
        await frames(4)
        service.stage.SetEditTarget(original_target)


async def test_recalled_selection_releases_previous_edit_without_clearing_review(service):
    adapter = adapter_for(service)
    first = await adapter.capture_viewpoint()
    second = await adapter.capture_viewpoint()
    original_target = service.stage.GetSessionLayer()
    service.stage.SetEditTarget(original_target)
    core = adapter.core
    try:
        await adapter.begin(first)
        recalled = core.get_markup_from_prim_path(second.markup_path)
        core.recall_markup(recalled, without_camera=True, force=True)
        try:
            await adapter.finish(first)
        except ValueError:
            pass
        else:
            raise AssertionError('Apply accepted evidence from a recalled replacement')
        assert core.editing_markup is None, 'The abandoned annotation remained in vendor edit mode'
        assert core.current_markup == recalled, 'Cleanup cleared the recalled review'
        assert service.stage.GetEditTarget().GetLayer() == original_target
    finally:
        editing = core.editing_markup
        if editing:
            core.end_edit_markup(editing, save=True, update_thumbnail=False)
        core.recall_markup(None)
        core.unlock_camera()
        adapter.destroy()
        service.stage.SetEditTarget(original_target)


async def test_destroy_during_creation_callback_releases_capture(service):
    import omni.kit.app
    manager = omni.kit.app.get_app().get_extension_manager()
    adapter = adapter_for(service)
    await adapter._ready()
    from omni.kit.markup.core import MarkupChangeCallbacks
    core = adapter.core
    stage = service.stage
    original_target = stage.GetSessionLayer()
    stage.SetEditTarget(original_target)
    task = None
    def cancel_and_destroy(*args):
        task.cancel()
        adapter.destroy()
        manager.set_extension_enabled_immediate('issues.tag', False)
    callback = MarkupChangeCallbacks(on_markup_created=cancel_and_destroy)
    core.register_callback(callback)
    try:
        task = asyncio.ensure_future(adapter.capture_viewpoint())
        try:
            await task
        except asyncio.CancelledError:
            pass
        else:
            raise AssertionError('Destroy did not cancel capture')
        assert core.editing_markup is None and core.current_markup is None
        assert stage.GetEditTarget().GetLayer() == original_target
    finally:
        core.deregister_callback(callback)
        editing = core.editing_markup
        if editing:
            core.end_edit_markup(editing, save=True, update_thumbnail=False)
        core.recall_markup(None)
        core.unlock_camera()
        adapter.destroy()
        stage.SetEditTarget(original_target)
        manager.set_extension_enabled_immediate('issues.tag', True)


async def test_replacement_edit_preserves_newer_explicit_target(service):
    from pxr import Sdf
    adapter, other = adapter_for(service), adapter_for(service)
    first = await adapter.capture_viewpoint()
    second = await adapter.capture_viewpoint()
    service.stage.SetEditTarget(service.stage.GetSessionLayer())
    choice = Sdf.Layer.CreateAnonymous('explicit-edit-target.usda')
    service.stage.GetSessionLayer().subLayerPaths.append(choice.identifier)
    try:
        await adapter.begin(first)
        service.stage.SetEditTarget(choice)
        await other.begin(second)
        try:
            await adapter.finish(first)
        except ValueError:
            pass
        await other.finish(second, save=False)
        assert service.stage.GetEditTarget().GetLayer() == choice, 'Replacement discarded the user-selected edit target'
    finally:
        adapter.destroy()
        other.destroy()
        service.stage.SetEditTarget(service.stage.GetRootLayer())
