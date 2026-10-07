"""Native Alt-drag navigation after recalling an imported BCF camera."""
from uuid import uuid4
from zipfile import ZipFile

import carb.settings
from pxr import Gf, Sdf, Usd, UsdGeom

from verify_kit import ROOT, enable_extension, frames


async def test_imported_bcf_orthographic_view_allows_orbit(service):
    assert enable_extension('omni.kit.ui_test')
    import omni.kit.ui_test as ui_test
    from carb.input import KeyboardEventType, KeyboardInput, MouseEventType
    from omni.kit.viewport.utility import get_active_viewport_window
    from issues_tag.bcf import apply_import, plan_import, read_bcf

    stage = service.stage
    UsdGeom.SetStageUpAxis(stage, 'Z')
    UsdGeom.SetStageMetersPerUnit(stage, 1)
    UsdGeom.Cube.Define(stage, '/OrbitLandmark')
    topic, view = str(uuid4()), str(uuid4())
    archive_path = ROOT / 'verification' / 'orbit-fixture.bcf'
    with ZipFile(archive_path, 'w') as archive:
        archive.writestr('bcf.version', '<Version VersionId="2.1"/>')
        archive.writestr(topic + '/markup.bcf', f'<Markup><Topic Guid="{topic}" TopicType="Issue" TopicStatus="Open"><Title>Orbit fixture</Title><CreationDate>2026-10-07T12:00:00Z</CreationDate><CreationAuthor>Verification</CreationAuthor></Topic><Viewpoints Guid="{view}"><Viewpoint>view.bcfv</Viewpoint></Viewpoints></Markup>')
        archive.writestr(topic + '/view.bcfv', f'<VisualizationInfo Guid="{view}"><OrthogonalCamera><CameraViewPoint><X>3</X><Y>4</Y><Z>12</Z></CameraViewPoint><CameraDirection><X>0</X><Y>0</Y><Z>-1</Z></CameraDirection><CameraUpVector><X>0</X><Y>1</Y><Z>0</Z></CameraUpVector><ViewToWorldScale>20</ViewToWorldScale></OrthogonalCamera></VisualizationInfo>')
    apply_import(plan_import(read_bcf(archive_path), service.store), {}, service)
    issue = next(issue for issue in service.list_issues() if issue.title == 'Orbit fixture')
    saved = service.store.get_viewpoint(issue.initial_viewpoint_id)
    window = get_active_viewport_window('Viewport')
    viewport = window.viewport_api
    previous_viewport = service.viewport._viewport
    previous_sync = viewport.lock_to_render_result
    settings = carb.settings.get_settings()
    keys = ('/persistent/exts/omni.kit.manipulator.camera/objectCentric/type',
            '/persistent/exts/omni.kit.manipulator.camera/objectCentric/useGroundPlane')
    previous_settings = [settings.get(key) for key in keys]
    try:
        service.viewport._viewport = viewport
        viewport.lock_to_render_result = False
        for key in keys:
            settings.set(key, 0)
        service.open_issue(issue.id)
        window.focus()
        await frames(10)
        camera = UsdGeom.Camera(stage.GetPrimAtPath(viewport.camera_path))
        assert camera.GetProjectionAttr().Get() == 'orthographic'
        # Native controller consumes this independently from cameraLock.
        assert camera.GetPrim().GetAttribute('omni:kit:orthoRotate').Get() is True
        with Usd.EditContext(stage, stage.GetSessionLayer()):
            camera.GetPrim().CreateAttribute('omni:kit:centerOfInterest', Sdf.ValueTypeNames.Vector3d).Set(Gf.Vec3d(0, 0, -12))
        before = camera.ComputeLocalToWorldTransform(viewport.time)
        from omni.kit.manipulator.camera import ViewportCameraManipulator
        controller = ViewportCameraManipulator(viewport)
        try:
            with Usd.EditContext(stage, stage.GetSessionLayer()):
                camera.GetPrim().GetAttribute('omni:kit:orthoRotate').Set(False)
            controller._on_began(controller.model)
            assert controller.model.get_as_ints('disable_tumble') == [1], 'Negative control must disable orthographic orbit'
            service.open_issue(issue.id)
            controller._on_began(controller.model)
            assert controller.model.get_as_ints('disable_tumble') == [0], 'Recall must enable the native orbit controller'
            item = controller.model.get_item('tumble')
            controller.model.set_floats(item, [-20, 10, 0])
            controller.model._item_changed(item)
            await frames(5)
            native_after = camera.ComputeLocalToWorldTransform(viewport.time)
            assert not Gf.IsClose(before.ExtractRotationMatrix(), native_after.ExtractRotationMatrix(), 1e-6), 'Native tumble command did not rotate the imported camera'
        finally:
            controller.destroy()
        # Check the UI input harness on a perspective baseline before relying on it.
        baseline = UsdGeom.Camera.Define(stage, '/OrbitInputBaseline')
        baseline.MakeMatrixXform().Set(Gf.Matrix4d().SetLookAt(Gf.Vec3d(10, 10, 10), Gf.Vec3d(0), Gf.Vec3d(0, 0, 1)).GetInverse())
        baseline.GetPrim().CreateAttribute('omni:kit:centerOfInterest', Sdf.ValueTypeNames.Vector3d).Set(Gf.Vec3d(0, 0, -17))
        viewport.camera_path = baseline.GetPath()
        await frames(10)
        frame = window.frame
        start = ui_test.Vec2(float(frame.screen_position_x) + float(frame.computed_width) * .55,
                            float(frame.screen_position_y) + float(frame.computed_height) * .55)
        end = ui_test.Vec2(start.x + 90, start.y + 30)

        async def orbit(active_camera, message):
            before_drag = active_camera.ComputeLocalToWorldTransform(viewport.time)
            await ui_test.input.emulate_mouse_move_and_click(start)
            await ui_test.input.emulate_keyboard(KeyboardEventType.KEY_PRESS, KeyboardInput.LEFT_ALT)
            await ui_test.human_delay()
            try:
                await ui_test.input.emulate_mouse(MouseEventType.MOVE, start)
                await ui_test.input.emulate_mouse(MouseEventType.LEFT_BUTTON_DOWN, start)
                await ui_test.input.emulate_mouse_slow_move(start, end)
            finally:
                await ui_test.input.emulate_mouse(MouseEventType.LEFT_BUTTON_UP, end)
                await ui_test.input.emulate_keyboard(KeyboardEventType.KEY_RELEASE, KeyboardInput.LEFT_ALT)
            await ui_test.human_delay()
            await frames(30)
            after_drag = active_camera.ComputeLocalToWorldTransform(viewport.time)
            assert not Gf.IsClose(before_drag.ExtractRotationMatrix(), after_drag.ExtractRotationMatrix(), 1e-6), message

        await orbit(baseline, 'Baseline Alt-drag did not orbit before issue recall')
        service.open_issue(issue.id)
        await frames(10)
        await orbit(camera, 'Alt-drag did not orbit the imported orthographic camera')
        assert camera.GetProjectionAttr().Get() == 'orthographic'
        assert service.store.get_viewpoint(saved.id) == saved, 'Navigation changed saved evidence'
        print('ISSUES_BCF_ORBIT_PASS', str(viewport.camera_path), flush=True)
    finally:
        service.viewport._viewport = previous_viewport
        viewport.lock_to_render_result = previous_sync
        for key, value in zip(keys, previous_settings):
            if value is None:
                settings.destroy_item(key)
            else:
                settings.set(key, value)
