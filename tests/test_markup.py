import asyncio
import importlib.util
import io
from pathlib import Path
from pxr import Gf, UsdGeom


def adapter_for(service):
    assert importlib.util.find_spec('issues_tag.markup'), 'Editable Markup evidence is not implemented'
    from issues_tag.markup import MarkupAdapter
    return MarkupAdapter(service)


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
