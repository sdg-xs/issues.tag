import importlib.util
from dataclasses import replace
from pxr import Gf, UsdGeom


def require_viewport():
    assert importlib.util.find_spec('issues_tag.viewport'), 'Saved review context is not implemented'


def test_imported_metadata_does_not_invalidate_coordinate_frame(service):
    from issues_tag.viewport import ViewportAdapter
    adapter = ViewportAdapter(service)
    saved = adapter.capture()
    incoming = replace(saved, coordinate_frame={**saved.coordinate_frame, 'bcf_default_visibility': True, 'bcf_visibility': []})
    try:
        adapter.restore(incoming)
    except ValueError as error:
        raise AssertionError('BCF metadata must not reject a matching scene coordinate frame') from error



async def test_viewpoint_restore_and_focus_independence(service):
    require_viewport()
    from issues_tag.viewport import ViewportAdapter
    from issues_tag.elements import reference_for_prim
    from omni.kit.viewport.utility import get_active_viewport
    from verify_kit import frames
    camera = UsdGeom.Camera.Define(service.stage, '/ReviewCamera')
    camera.AddTranslateOp().Set(Gf.Vec3d(0, 0, 10))
    cube = UsdGeom.Cube.Define(service.stage, '/Cube')
    viewport = get_active_viewport()
    assert viewport, 'Verification app needs a real viewport'
    viewport.camera_path = '/ReviewCamera'
    await frames(10)
    adapter = ViewportAdapter(service, viewport)
    original_viewport = service.viewport
    service.viewport = adapter
    try:
        service._context.get_selection().set_selected_prim_paths(['/Cube'], False)
        saved = adapter.capture()
        issue = service.create_issue('Saved view', viewpoint=saved)
        camera.GetFocalLengthAttr().Set(80)
        cube.GetVisibilityAttr().Set('invisible')
        service._context.get_selection().set_selected_prim_paths([], False)
        service.open_issue(issue)
        restored = UsdGeom.Camera(service.stage.GetPrimAtPath(viewport.camera_path))
        assert abs(restored.GetFocalLengthAttr().Get() - saved.camera['focal_length']) < 1e-6
        assert cube.ComputeVisibility() != 'invisible'
        assert service._context.get_selection().get_selected_prim_paths() == ['/Cube']
        service.set_related_elements(issue, (reference_for_prim(service.stage, '/Cube'),))
        service.focus_related(issue)
        assert service.store.get_viewpoint(saved.id) == saved
    finally:
        service.viewport = original_viewport
        adapter.destroy()


def test_pin_filtering_and_issue_access(service):
    require_viewport()
    from issues_tag.viewport import pin_is_visible
    from issues_tag.elements import make_anchor
    cube = UsdGeom.Cube.Define(service.stage, '/Cube')
    anchor = make_anchor(service.stage, '/Cube', (0, 0, 1))
    issue = service.create_issue('Hidden attachment', anchor)
    assert pin_is_visible(service.stage, anchor, ())
    cube.GetVisibilityAttr().Set('invisible')
    assert not pin_is_visible(service.stage, anchor, ())
    cube.GetVisibilityAttr().Set('inherited')
    assert not pin_is_visible(service.stage, anchor, ((0, 0, -1, 0),))
    assert len(service.list_issues()) == 1


async def test_surface_pick_and_placement_lifecycle(service):
    from issues_tag.viewport import ViewportAdapter
    from omni.kit.viewport.utility import get_active_viewport
    from verify_kit import frames
    camera = UsdGeom.Camera.Define(service.stage, '/PickCamera')
    camera.AddTranslateOp().Set(Gf.Vec3d(0, 0, 10))
    UsdGeom.Cube.Define(service.stage, '/PickedCube')
    viewport = get_active_viewport()
    viewport.camera_path = '/PickCamera'
    await frames(30)
    adapter = ViewportAdapter(service, viewport)
    assert callable(getattr(adapter, 'start', None)), 'Native issue pin overlay is missing'
    adapter.start()
    anchor = await adapter.pick(0, 0)
    assert anchor and anchor.element.prim_path == '/PickedCube', 'Placement must query the rendered surface'
    assert abs(anchor.local_position[2] - 1) < 0.05
    placement = adapter.begin_placement()
    assert not placement.done()
    await adapter._place_at(viewport, (0, 0))
    placed = await placement
    assert placed.element.prim_path == '/PickedCube'
    placement = adapter.begin_placement()
    adapter.destroy()
    assert placement.cancelled(), 'Shutdown must cancel pending placement'


async def test_overlay_tracks_scene_and_stage_scope(service):
    from issues_tag.viewport import ViewportAdapter
    from issues_tag.elements import make_anchor
    from omni.kit.viewport.utility import get_active_viewport
    from verify_kit import frames
    cube = UsdGeom.Cube.Define(service.stage, '/PinCube')
    issue = service.create_issue('Visible pin', make_anchor(service.stage, '/PinCube', (0, 0, 1)))
    adapter = ViewportAdapter(service, get_active_viewport())
    assert callable(getattr(adapter, 'start', None)), 'Native issue pin overlay is missing'
    adapter.start()
    await frames(5)
    assert any(issue in item.visible_issue_ids for item in adapter._items), 'Visible issue must have a viewport pin'
    cube.GetVisibilityAttr().Set('invisible')
    await frames(5)
    assert all(issue not in item.visible_issue_ids for item in adapter._items)
    await service._context.new_stage_async()
    await frames(5)
    assert all(not item.visible_issue_ids for item in adapter._items)
    adapter.destroy()

async def test_restore_clipping_and_viewport_camera_isolation(service):
    from issues_tag.viewport import ViewportAdapter, ENABLED, PLANES
    from omni.kit.viewport.utility import get_active_viewport, create_viewport_window
    from pxr import Sdf, Usd
    from verify_kit import frames
    primary = get_active_viewport()
    for path in ('/PrimaryCamera', '/OtherCamera'):
        camera = UsdGeom.Camera.Define(service.stage, path)
        camera.AddTranslateOp().Set(Gf.Vec3d(0, 0, 10))
    primary.camera_path = '/PrimaryCamera'
    other = create_viewport_window('Issues isolation test', width=320, height=240, camera_path='/OtherCamera')
    assert other
    await frames(10)
    adapter = ViewportAdapter(service, primary)
    with Usd.EditContext(service.stage, service.stage.GetSessionLayer()):
        render = service.stage.GetPrimAtPath(primary.render_product_path)
        render.CreateAttribute(ENABLED, Sdf.ValueTypeNames.Bool).Set(True)
        render.CreateAttribute(PLANES, Sdf.ValueTypeNames.FloatArray).Set([0, 0, 1, 0])
    saved = adapter.capture()
    assert saved.clipping_planes == ((0, 0, 1, 0),)
    render.GetAttribute(ENABLED).Set(False)
    adapter.restore(saved)
    assert adapter.clipping_planes(primary) == saved.clipping_planes
    assert str(other.viewport_api.camera_path) == '/OtherCamera', 'Restoring review must preserve the other viewport camera'
    adapter.destroy()
    other.destroy()

async def preview_issue_pins(service):
    from pathlib import Path
    import omni.appwindow
    import omni.kit.renderer_capture
    from omni.kit.viewport.utility import get_active_viewport_window, next_viewport_frame_async
    from issues_tag.model import Status
    from pxr import UsdLux
    from issues_tag.viewport import ViewportAdapter
    from issues_tag.elements import make_anchor
    from verify_kit import frames
    stage = service.stage
    camera = UsdGeom.Camera.Define(stage, '/PinEvidenceCamera')
    camera.AddTranslateOp().Set(Gf.Vec3d(0, 0, 10))
    camera.GetFocalLengthAttr().Set(35)
    UsdLux.DomeLight.Define(stage, '/PinEvidenceLight').GetIntensityAttr().Set(1000)
    for name, x, z, color in (('Front', -1.5, 1, (.6, .7, .72)), ('Behind', 1.5, -2, (.2, .7, .6))):
        cube = UsdGeom.Cube.Define(stage, '/' + name)
        cube.AddTranslateOp().Set(Gf.Vec3d(x, 0, z))
        cube.GetDisplayColorAttr().Set([color])
        issue = service.create_issue(name + ' surface issue', make_anchor(stage, '/' + name, (x, 0, z + 1)))
        if name == 'Behind':
            service.set_status(issue, Status.IN_PROGRESS)
    # Cover the right-hand attachment in rendered geometry. Its UI pin must remain visible.
    cover = UsdGeom.Cube.Define(stage, '/Cover')
    cover.AddTranslateOp().Set(Gf.Vec3d(1.5, 0, 2))
    cover.GetDisplayColorAttr().Set([(.3, .35, .4)])
    viewport = get_active_viewport_window('Viewport')
    viewport.viewport_api.camera_path = camera.GetPath()
    adapter = ViewportAdapter(service, viewport.viewport_api)
    adapter.start()
    try:
        await frames(45)
        await next_viewport_frame_async(viewport.viewport_api, 3)
        assert any(len(item.visible_issue_ids) == 2 for item in adapter._items)
        path = Path(__file__).resolve().parent.parent / 'verification' / 'issues-pins.png'
        if path.exists():
            path.unlink()
        renderer = omni.kit.renderer_capture.acquire_renderer_capture_interface()
        app_window = omni.appwindow.get_default_app_window()
        renderer.capture_next_frame_swapchain_to_file(str(path), app_window, {'format': 'png'})
        await frames(1)
        renderer.wait_async_capture(app_window)
        await frames(10)
        assert path.exists() and path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    finally:
        adapter.destroy()

async def preview_native_gesture_placement(service):
    """Visible acceptance: a native mouse event must complete surface placement."""
    import asyncio
    import omni.kit.app
    from omni.kit.viewport.utility import create_viewport_window, next_viewport_frame_async
    from issues_tag.viewport import ViewportAdapter
    from verify_kit import frames

    from verify_kit import enable_extension
    assert enable_extension('omni.kit.ui_test')
    from omni.kit.ui_test import Vec2, emulate_mouse_move_and_click

    stage = service.stage
    camera = UsdGeom.Camera.Define(stage, '/NativeGestureCamera')
    camera.AddTranslateOp().Set(Gf.Vec3d(0, 0, 10))
    camera.GetFocalLengthAttr().Set(35)
    UsdGeom.Cube.Define(stage, '/NativeGestureCube')
    UsdGeom.Cube.Define(stage, '/SelectionBeforePlacement').AddTranslateOp().Set(Gf.Vec3d(5, 0, 0))
    selection = service._context.get_selection()
    selection.set_selected_prim_paths(['/SelectionBeforePlacement'], False)
    before = tuple(selection.get_selected_prim_paths())
    window = create_viewport_window('Native issue placement regression', width=640, height=480,
                                    position_x=20, position_y=20, camera_path=camera.GetPath())
    assert window and window.visible
    window.focus()
    adapter = service.viewport
    previous_viewport = adapter._viewport
    previous_callback = adapter.on_pin_clicked
    adapter._viewport = window.viewport_api
    clicked = []
    adapter.on_pin_clicked = clicked.append
    try:
        adapter.start()
        await frames(30)
        await asyncio.wait_for(next_viewport_frame_async(window.viewport_api, 1), 15)
        adapter.begin_placement()
        await frames(5)
        adapter.cancel_placement()
        pending = adapter.begin_placement()
        await frames(5)
        frame = window.frame
        await asyncio.sleep(.6)
        center = Vec2(float(frame.screen_position_x) + float(frame.computed_width) / 2,
                      float(frame.screen_position_y) + float(frame.computed_height) / 2)
        print('NATIVE_GESTURE_CLICK', center, flush=True)
        # Exercise the app input provider rather than invoking the pick handler.
        await asyncio.wait_for(emulate_mouse_move_and_click(center), 15)
        anchor = await asyncio.wait_for(pending, 15)
        assert anchor and anchor.element.prim_path == '/NativeGestureCube', 'Native click did not complete surface placement'
        assert abs(anchor.local_position[2] - 1) < .05
        issue_id = service.create_issue('Native viewport click issue', anchor)
        assert service.get_issue(issue_id).anchor == anchor
        assert tuple(selection.get_selected_prim_paths()) == before, 'Placement click changed ordinary model selection'
        await frames(5)
        await asyncio.sleep(.6)
        await asyncio.wait_for(emulate_mouse_move_and_click(center), 15)
        await frames(5)
        assert clicked == [issue_id], f'Clicking the lettered pin must open its issue; got {clicked}'
    finally:
        adapter.cancel_placement()
        adapter._viewport = previous_viewport
        adapter.on_pin_clicked = previous_callback
        window.destroy()
        await frames(5)


async def test_pin_updates_reuse_unchanged_model_and_invalidate_edits(service):
    from unittest.mock import patch
    from issues_tag import viewport as module
    from issues_tag.elements import make_anchor
    from issues_tag.model import Status
    from omni.kit.viewport.utility import get_active_viewport
    from verify_kit import frames
    from fixtures import two_buildings
    two_buildings(service.stage)
    issue = service.create_issue('Cached pin', make_anchor(service.stage, '/A/Cube', (0, 0, 1)))
    adapter = module.ViewportAdapter(service, get_active_viewport())
    adapter.start()
    try:
        await frames(5)
        item = next(item for item in adapter._items if item.viewport_api == adapter.viewport)
        assert issue in item.visible_issue_ids
        with patch.object(module, 'world_anchor', wraps=module.world_anchor) as validation:
            for _ in range(100):
                item.sync()
            assert validation.call_count == 0, 'Unchanged viewport frames must reuse validated anchors'
        service.set_status(issue, Status.CLOSED)
        await frames(5)
        assert any(pin[0] == issue and pin[2] == Status.CLOSED for pin in item.pins)
        transform = UsdGeom.Xformable(service.stage.GetPrimAtPath('/A')).AddTranslateOp()
        transform.Set(Gf.Vec3d(10, 0, 0))
        await frames(5)
        assert next(pin[1] for pin in item.pins if pin[0] == issue) == (10, 0, 1)
        duplicate = UsdGeom.Cube.Define(service.stage, '/A/Duplicate').GetPrim()
        from pxr import Sdf
        duplicate.CreateAttribute('ifc:GlobalId', Sdf.ValueTypeNames.String).Set('element-A')
        await frames(5)
        assert issue not in item.visible_issue_ids, 'Duplicate source identities must invalidate cached pins'
        duplicate.SetActive(False)
        await frames(5)
        assert issue in item.visible_issue_ids
        UsdGeom.Cube(service.stage.GetPrimAtPath('/A/Cube')).GetSizeAttr().Set(9)
        await frames(5)
        assert issue not in item.visible_issue_ids, 'Changed geometry must not retain a verified pin'
    finally:
        adapter.destroy()


async def test_placement_cancel_clears_prompt_without_creating_issue(service):
    from issues_tag.viewport import ViewportAdapter
    from omni.kit.viewport.utility import get_active_viewport
    from verify_kit import frames
    adapter = ViewportAdapter(service, get_active_viewport())
    transitions = []
    service.add_listener(lambda: transitions.append(adapter.is_placing))
    adapter.start()
    try:
        pending = adapter.begin_placement()
        assert adapter.is_placing
        adapter.cancel_placement()
        assert pending.cancelled() and not adapter.is_placing
        await frames(2)
        assert transitions[0] is True and transitions[-1] is False
        assert service.list_issues() == ()
        pending = adapter.begin_placement()
        await service._context.new_stage_async()
        await frames(5)
        assert pending.cancelled() and not adapter.is_placing
    finally:
        adapter.destroy()


async def test_pin_cache_tracks_camera_parent_geometry(service):
    from issues_tag.viewport import ViewportAdapter
    from issues_tag.elements import make_anchor
    from omni.kit.viewport.utility import get_active_viewport
    from verify_kit import frames
    parent = UsdGeom.Camera.Define(service.stage, '/AnchorParent')
    UsdGeom.Cube.Define(service.stage, '/AnchorParent/Cube')
    issue = service.create_issue('Geometry under camera', make_anchor(service.stage, '/AnchorParent/Cube', (0, 0, 1)))
    adapter = ViewportAdapter(service, get_active_viewport())
    adapter.start()
    try:
        await frames(5)
        item = next(item for item in adapter._items if item.viewport_api == adapter.viewport)
        parent.AddTranslateOp().Set(Gf.Vec3d(10, 0, 0))
        await frames(5)
        assert next(pin[1] for pin in item.pins if pin[0] == issue) == (10, 0, 1)
        parent.GetVisibilityAttr().Set('invisible')
        await frames(5)
        assert issue not in item.visible_issue_ids
        parent.GetVisibilityAttr().Set('inherited')
        await frames(5)
        assert issue in item.visible_issue_ids
        parent.GetPrim().SetActive(False)
        await frames(5)
        assert issue not in item.visible_issue_ids
    finally:
        adapter.destroy()


async def test_completed_pick_cannot_cross_scene_close(service):
    import asyncio
    from issues_tag.viewport import ViewportAdapter
    from issues_tag.elements import make_anchor
    from omni.kit.viewport.utility import get_active_viewport
    from verify_kit import frames
    UsdGeom.Cube.Define(service.stage, '/Cube')
    anchor = make_anchor(service.stage, '/Cube', (0, 0, 1))
    adapter = ViewportAdapter(service, get_active_viewport())
    task = asyncio.ensure_future(adapter.request_placement())
    try:
        await frames(1)
        adapter._placement.set_result(anchor)
        service._context.close_stage()
        assert await task is None, 'Completed picks from a closed scene must be discarded before creation'
    finally:
        adapter.destroy()


async def test_queued_click_cannot_complete_replacement_placement(service):
    import asyncio
    from unittest.mock import AsyncMock, patch
    from issues_tag.viewport import ViewportAdapter
    from issues_tag.elements import make_anchor
    from omni.kit.viewport.utility import get_active_viewport
    UsdGeom.Cube.Define(service.stage, '/Cube')
    anchor = make_anchor(service.stage, '/Cube', (0, 0, 1))
    adapter = ViewportAdapter(service, get_active_viewport())
    try:
        first = adapter.begin_placement()
        with patch.object(adapter, 'pick', new=AsyncMock(return_value=anchor)) as raycast:
            queued = asyncio.ensure_future(adapter._place_at(adapter.viewport, (0, 0), first))
            adapter.cancel_placement()
            replacement = adapter.begin_placement()
            await queued
            assert not replacement.done(), 'A queued old click must not consume a replacement placement'
            assert raycast.await_count == 0, 'A canceled placement must not query the new scene'
    finally:
        adapter.destroy()
