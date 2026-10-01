"""Native saved Markup camera recall without rendering a thumbnail."""
import importlib
from dataclasses import replace

from pxr import Gf, Sdf, Usd, UsdGeom

from verify_kit import enable_extension, frames


async def test_saved_native_issue_view_recalls_camera_without_annotation(service):
    await exercise_saved_view(service)


async def test_saved_native_parent_camera_uses_portable_world_pose(service):
    await exercise_saved_view(service, transformed_parent=True)


async def test_saved_native_shared_camera_preserves_other_viewport(service):
    from omni.kit.viewport.utility import create_viewport_window
    viewport = service.viewport.viewport
    previous = service.viewport._viewport
    service.viewport._viewport = viewport
    other = create_viewport_window('Native recall shared camera', width=320, height=240,
                                   camera_path='/OmniverseKit_Persp')
    try:
        await exercise_saved_view(service, other=other)
    finally:
        other.destroy()
        service.viewport._viewport = previous


async def preview_native_saved_view_allows_mouse_navigation(service):
    from omni.kit.viewport.utility import get_active_viewport_window
    viewport = get_active_viewport_window('Viewport').viewport_api
    previous = viewport.lock_to_render_result
    try:
        # SDK input tests detach frame synchronization for deterministic gestures.
        viewport.lock_to_render_result = False
        await exercise_mouse_navigation(service)
    finally:
        viewport.lock_to_render_result = previous


async def exercise_mouse_navigation(service):
    import asyncio
    from omni.kit.viewport.utility import get_active_viewport_window
    assert enable_extension('omni.kit.ui_test')
    from omni.kit.ui_test import Vec2, emulate_mouse_move_and_click, emulate_mouse_scroll
    from omni.kit.viewport.registry import RegisterScene
    assert any(name == 'omni.kit.viewport.window.manipulator.Camera'
               for name, _ in RegisterScene.ordered_factories(())), 'Native camera controller was not registered'
    window = get_active_viewport_window('Viewport')
    baseline = UsdGeom.Camera.Define(service.stage, '/BaselineNavigationCamera')
    baseline.MakeMatrixXform().Set(Gf.Matrix4d().SetTranslate(Gf.Vec3d(0, 0, 10)))
    window.viewport_api.camera_path = baseline.GetPath()
    window.focus()
    await frames(10)
    async def navigate(camera, message):
        # Independent scroll gestures must exceed the SDK's 0.4-second coalescing window.
        await asyncio.sleep(.6)
        frame = window.frame
        center = Vec2(float(frame.screen_position_x) + float(frame.computed_width) / 2,
                      float(frame.screen_position_y) + float(frame.computed_height) / 2)
        before = camera.ComputeLocalToWorldTransform(window.viewport_api.time)
        await emulate_mouse_move_and_click(center)
        await emulate_mouse_scroll(Vec2(0, 1000))
        for _ in range(100):
            await frames(1)
            after = camera.ComputeLocalToWorldTransform(window.viewport_api.time)
            if not Gf.IsClose(before, after, 1e-6):
                break
        assert not Gf.IsClose(before, after, 1e-6), message
    await navigate(baseline, 'Baseline mouse navigation failed before opening any issue')
    record = await exercise_saved_view(service)
    camera = UsdGeom.Camera(service.stage.GetPrimAtPath(window.viewport_api.camera_path))
    await navigate(camera, 'Mouse wheel must navigate after opening native issue evidence')
    assert service.store.get_viewpoint(record.id).camera == record.camera
    from issues_tag.markup import MarkupAdapter
    adapter = MarkupAdapter(service)
    try:
        assert enable_extension('omni.kit.tool.markup'), 'Private Markup Tool cannot activate'
        evidence = await adapter.capture_viewpoint()
        await adapter.begin(evidence)
        adapter.core.add_element(20, 20, 70, 70, 'Arrow',
            {'Markup.Viewport.Arrow': {'color': 0xff0000ff, 'border_width': 5}, 'ArrowDirection': 1}, color=-16776961)
        evidence = await adapter.finish(evidence)
        issue_id = service.create_issue('Navigation after annotation', viewpoint=evidence)
        service.open_issue(issue_id)
        await frames(5)
        camera = UsdGeom.Camera(service.stage.GetPrimAtPath(window.viewport_api.camera_path))
        await navigate(camera, 'Completed annotation must release viewport mouse navigation')
        assert adapter.core.current_markup is None and adapter.core.editing_markup is None
        assert service.store.get_viewpoint(evidence.id).camera == evidence.camera
    finally:
        adapter.destroy()


def saved_scene_content(stage):
    copied = Sdf.Layer.CreateAnonymous()
    for path in ('/Issues', '/Viewport_Markups', '/SavedSourceCamera', '/CameraParent', '/SelectedCube', '/HiddenCube'):
        if stage.GetRootLayer().GetPrimAtPath(path):
            Sdf.CopySpec(stage.GetRootLayer(), path, copied, path)
    return copied.ExportToString()


async def exercise_saved_view(service, transformed_parent=False, other=None):
    from issues_tag.elements import reference_for_prim
    stage = service.stage
    viewport = service.viewport.viewport
    camera_path = '/CameraParent/SavedSourceCamera' if transformed_parent else '/SavedSourceCamera'
    if transformed_parent:
        UsdGeom.Xform.Define(stage, '/CameraParent').AddTranslateOp().Set(Gf.Vec3d(20, 0, 0))
    camera = UsdGeom.Camera.Define(stage, camera_path)
    camera.MakeMatrixXform().Set(Gf.Matrix4d().SetTranslate(Gf.Vec3d(3, 4, 12)))
    camera.GetFocalLengthAttr().Set(37)
    viewport.camera_path = camera_path
    UsdGeom.Cube.Define(stage, '/SelectedCube')
    hidden = UsdGeom.Cube.Define(stage, '/HiddenCube')
    hidden.GetVisibilityAttr().Set('invisible')
    await frames(8)
    record = service.viewport.capture()
    markup_path = '/Viewport_Markups/RecallFixture'
    prim = stage.DefinePrim(markup_path, 'Scope')
    for name, value in [('camera:path', camera_path), ('created', '2026-09-30'),
                        ('created_by', 'Verification'), ('comment', 'Saved native camera fixture')]:
        prim.CreateAttribute(name, Sdf.ValueTypeNames.String).Set(value)
    prim.CreateAttribute('frame', Sdf.ValueTypeNames.Float).Set(0)
    prim.CreateAttribute('approval', Sdf.ValueTypeNames.Int).Set(0)
    prim.CreateAttribute('icon_position', Sdf.ValueTypeNames.Float3).Set(Gf.Vec3f(0))
    saved = stage.DefinePrim(markup_path + '/SavedSourceCamera')
    for attr in camera.GetPrim().GetAttributes():
        value = attr.Get()
        if value is not None:
            saved.CreateAttribute(attr.GetName(), attr.GetTypeName()).Set(value)
    saved.CreateAttribute('omni:kit:cameraLock', Sdf.ValueTypeNames.Bool).Set(True)
    with Usd.EditContext(stage, stage.GetSessionLayer()):
        shared = UsdGeom.Camera.Define(stage, '/OmniverseKit_Persp')
        shared_pose = Gf.Matrix4d().SetTranslate(Gf.Vec3d(90, 80, 70))
        shared.MakeMatrixXform().Set(shared_pose)
    assert enable_extension('omni.kit.markup.core')
    core = importlib.import_module('omni.kit.markup.core').get_instance()
    core.load_markups()
    await frames(5)
    assert core.get_markup_from_prim_path(markup_path)
    record = replace(record, markup_path=markup_path, selection=(reference_for_prim(stage, '/SelectedCube'),))
    issue_id = service.create_issue('Native saved view', viewpoint=record)
    hidden.GetVisibilityAttr().Set('inherited')
    camera.MakeMatrixXform().Set(Gf.Matrix4d().SetTranslate(Gf.Vec3d(30, 40, 120)))
    before = saved_scene_content(stage)
    service.open_issue(issue_id)
    await frames(5)
    if other is not None:
        assert str(viewport.camera_path).startswith('/IssuesReviewCamera_')
    else:
        assert str(viewport.camera_path) == '/OmniverseKit_Persp'
    restored = UsdGeom.Camera(stage.GetPrimAtPath(viewport.camera_path))
    expected = Gf.Matrix4d().SetTranslate(Gf.Vec3d(23 if transformed_parent else 3, 4, 12))
    assert Gf.IsClose(restored.ComputeLocalToWorldTransform(Usd.TimeCode.Default()), expected, 1e-6)
    assert restored.GetFocalLengthAttr().Get() == 37
    assert stage.GetPrimAtPath(viewport.camera_path).GetAttribute('omni:kit:cameraLock').Get() is False
    if other:
        assert str(other.viewport_api.camera_path) == '/OmniverseKit_Persp'
        assert Gf.IsClose(shared.ComputeLocalToWorldTransform(Usd.TimeCode.Default()), shared_pose, 1e-6)
    assert core.current_markup is None and core.editing_markup is None
    assert hidden.ComputeVisibility() == 'invisible'
    assert service._context.get_selection().get_selected_prim_paths() == ['/SelectedCube']
    after = saved_scene_content(stage)
    if after != before:
        import difflib
        raise AssertionError('Recall changed saved issues, evidence, model, or source camera:\n' + '\n'.join(difflib.unified_diff(before.splitlines(), after.splitlines())))
    with Usd.EditContext(stage, stage.GetSessionLayer()):
        moved = Gf.Matrix4d().SetTranslate(Gf.Vec3d(5, 6, 14))
        restored.MakeMatrixXform().Set(moved)
    await frames(5)
    assert Gf.IsClose(restored.ComputeLocalToWorldTransform(Usd.TimeCode.Default()), moved, 1e-6)
    assert service.store.get_viewpoint(record.id).camera == record.camera
    assert core.current_markup is None and core.editing_markup is None
    return record
