"""Selected, visible Kit acceptance for standard BCF camera review."""
import asyncio
import difflib
import json
import math
import sys
from uuid import uuid4
from zipfile import ZipFile

import omni.usd
from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux

from verify_kit import APP, ROOT, frames


ARTIFACTS = ROOT / 'verification' / 'bcf-camera'


def _phase(name, **values):
    ARTIFACTS.mkdir(exist_ok=True)
    payload = dict(phase=name, **values)
    with (ARTIFACTS / 'milestones.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(payload) + '\n')
    print('ISSUES_CAMERA_PHASE', json.dumps(payload), flush=True)


def _assert_preview_log_clean():
    log = (ROOT / 'verification' / 'kit.log').read_text(encoding='utf-8', errors='replace')
    errors = [line for line in log.splitlines() if '[Error]' in line
              and ('IssuesImportPreview_' in line or '[omni.ui' in line)]
    assert not errors, '\n'.join(errors)


def _model(stage, name, units, axis):
    source = Usd.Stage.CreateInMemory()
    UsdGeom.SetStageMetersPerUnit(source, units)
    UsdGeom.SetStageUpAxis(source, axis)
    UsdGeom.SetStageMetersPerUnit(stage, units)
    UsdGeom.SetStageUpAxis(stage, axis)
    root = UsdGeom.Xform.Define(source, '/Model')
    source.SetDefaultPrim(root.GetPrim())
    site = UsdGeom.Xform.Define(source, '/Model/Site')
    site.GetPrim().CreateAttribute('omni:hoops:metadata:TYPE', Sdf.ValueTypeNames.String).Set('IFCSITE')
    site.AddTranslateOp().Set((100 / units, 200 / units, 0))

    def source_point(point):
        x, y, z = point
        return Gf.Vec3d(x, z, -y) / units if axis == 'Y' else Gf.Vec3d(x, y, z) / units

    points = ((-2.5, -1, 0), (2, -1, 0), (0, 2, 0))
    paths = []
    for label, point, color, kind in zip(('Red', 'Green', 'Blue'), points,
            ((1, .01, .01), (.01, 1, .01), (.01, .01, 1)), (UsdGeom.Cube, UsdGeom.Sphere, UsdGeom.Cube)):
        geometry = kind.Define(source, '/Model/Site/' + label)
        if kind == UsdGeom.Cube:
            geometry.GetSizeAttr().Set(1.4 / units)
        else:
            geometry.GetRadiusAttr().Set(.85 / units)
        geometry.AddTranslateOp().Set(source_point(point))
        geometry.GetDisplayColorAttr().Set([color])
        paths.append('/Model/Site/' + label)
    source_path = ARTIFACTS / (name + '-source.usda')
    source.GetRootLayer().Export(str(source_path))
    instance = UsdGeom.Xform.Define(stage, '/Model')
    instance.GetPrim().GetReferences().AddReference(str(source_path))
    instance.AddRotateZOp().Set(90)
    light = UsdLux.DomeLight.Define(stage, '/FixtureLight')
    light.GetIntensityAttr().Set(1000)
    reference = stage.GetPrimAtPath('/Model/Site')
    world = UsdGeom.XformCache().GetLocalToWorldTransform(reference)
    position = world.Transform(source_point((0, 0, 12)))
    right = world.TransformDir(source_point((1, 0, 0))).GetNormalized()
    up = world.TransformDir(source_point((0, 1, 0))).GetNormalized()
    back = world.TransformDir(source_point((0, 0, 1))).GetNormalized()
    expected = Gf.Matrix4d(*right, 0, *up, 0, *back, 0, *position, 1)
    landmarks = [world.Transform(source_point(point)) for point in points]
    return source_path, paths, expected, landmarks


async def _capture(viewport, name):
    from omni.kit.viewport.utility import capture_viewport_to_file, next_viewport_frame_async
    _phase('before_capture', artifact=name, camera=str(viewport.camera_path))
    await frames(30)
    await asyncio.wait_for(next_viewport_frame_async(viewport, 2), 30)
    path = ARTIFACTS / (name + '.png')
    capture = capture_viewport_to_file(viewport, str(path))
    await asyncio.wait_for(capture.wait_for_result(completion_frames=15), 45)
    assert path.is_file() and path.stat().st_size > 1000, str(path)
    _phase('capture_complete', artifact=str(path))
    return path


def _landmark_pixels(path):
    from PIL import Image
    with Image.open(path) as image:
        image = image.convert('RGB')
        width, height = image.size
        totals = [[0, 0, 0] for _ in range(3)]
        for index, pixel in enumerate(image.getdata()):
            for channel in range(3):
                other = [pixel[c] for c in range(3) if c != channel]
                if pixel[channel] > 75 and pixel[channel] > max(other) * 1.45:
                    totals[channel][0] += index % width
                    totals[channel][1] += index // width
                    totals[channel][2] += 1
        assert all(count > 80 for _, _, count in totals), (path, totals)
        return [(x / count / width, y / count / height) for x, y, count in totals]


def _archive(name, snapshot, axis):
    path = ARTIFACTS / (name + '.bcf')
    identities = [(str(uuid4()), str(uuid4()), str(uuid4())) for _ in range(2)]
    positions = [(0, 0, 12), (100, 200, 12) if axis == 'Z' else (100, 0, 212)]
    with ZipFile(path, 'w') as archive:
        archive.writestr('bcf.version', '<Version VersionId="2.1"/>')
        for label, (topic, view, comment), position in zip(('Local', 'World'), identities, positions):
            vectors = ''.join('<' + key + '>' + ''.join(f'<{axis}>{number}</{axis}>' for axis, number in zip('XYZ', values)) + '</' + key + '>' for key, values in (
                ('CameraViewPoint', position), ('CameraDirection', (0, 0, -1)), ('CameraUpVector', (0, 1, 0))))
            archive.writestr(topic + '/view.bcfv', f'<VisualizationInfo Guid="{view}"><PerspectiveCamera>{vectors}<FieldOfView>60</FieldOfView></PerspectiveCamera></VisualizationInfo>')
            archive.writestr(topic + '/snapshot.png', snapshot)
            archive.writestr(topic + '/markup.bcf', f'<Markup><Topic Guid="{topic}" TopicType="Issue" TopicStatus="Open"><Title>{label} fixture</Title><Description>Synthetic camera acceptance</Description><CreationDate>2026-10-07T10:00:00Z</CreationDate><CreationAuthor>Verification</CreationAuthor></Topic><Comment Guid="{comment}"><Date>2026-10-07T10:00:00Z</Date><Author>Verification</Author><Comment>Preserve this comment</Comment><Viewpoint Guid="{view}"/></Comment><Viewpoints Guid="{view}"><Viewpoint>view.bcfv</Viewpoint><Snapshot>snapshot.png</Snapshot></Viewpoints></Markup>')
    return path, identities


async def _open_review(controller, path):
    from issues_tag.import_window import ImportWindow
    controller.file_dialog(False)
    picker = controller._dialogs[-1]
    picker.set_current_directory(str(path.parent))
    picker.set_filename(path.name)
    picker._click_apply_handler(path.name, str(path.parent))
    await frames(10)
    review = controller._dialogs[-1]
    assert isinstance(review, ImportWindow), getattr(controller._window, '_error', '')
    assert hasattr(review, '_coordinate_model'), 'Native camera controls failed to build'
    assert review._provider is not None, 'Source snapshot failed to build'
    return review


async def _correct(review, identity, local):
    review.select_viewpoint(identity)
    await frames(3)
    review._reference_model.get_item_value_model().set_value(review._reference_choices.index('/Model/Site'))
    review._coordinate_model.get_item_value_model().set_value(int(local))
    review._fov_model.get_item_value_model().set_value(1)
    assert review._camera_options_dirty
    assert not review._preview_button.enabled and not review._apply_button.enabled
    review._replan_clicked()
    await frames(3)
    assert not review._error, review._error
    assert not review._camera_options_dirty


async def _assert_preview(review, viewport, expected, landmarks, baseline, name):
    review._preview_clicked()
    await frames(5)
    assert not review._error, review._error
    camera = UsdGeom.Camera(viewport.stage.GetPrimAtPath(viewport.camera_path))
    assert str(viewport.camera_path).startswith('/IssuesImportPreview_')
    assert Gf.IsClose(camera.ComputeLocalToWorldTransform(Usd.TimeCode.Default()), expected, 1e-5)
    frustum = camera.GetCamera(Usd.TimeCode.Default()).frustum
    projection = frustum.ComputeViewMatrix() * frustum.ComputeProjectionMatrix()
    projected = []
    for point in landmarks:
        ndc = projection.Transform(point)
        assert all(-1 < value < 1 for value in ndc), ('Landmark outside frustum', point, ndc)
        projected.append(((ndc[0] + 1) / 2, (1 - ndc[1]) / 2))
    artifact = await _capture(viewport, name)
    actual = _landmark_pixels(artifact)
    expected_pixels = _landmark_pixels(baseline)
    for measured, original, geometric in zip(actual, expected_pixels, projected):
        assert math.dist(measured, original) < .025, (measured, original)
        assert math.dist(measured, geometric) < .045, (measured, geometric)
    _phase('landmarks_verified', artifact=str(artifact), centroids=actual, projected=projected)
    return str(viewport.camera_path)


async def _scenario(service, name, units=1, axis='Z'):
    from omni.kit.viewport.utility import get_active_viewport_window
    from test_ui import controller_for, close_controller
    from issues_tag.store import IssueStore
    _phase('scene', scenario=name, python=sys.version, usd=Usd.GetVersion(), kit=APP.get_build_version())
    stage = service.stage
    source_path, paths, expected, landmarks = _model(stage, name, units, axis)
    source_bytes = source_path.read_bytes()
    window = get_active_viewport_window('Viewport')
    assert window and window.visible
    viewport = window.viewport_api
    viewport.resolution = (800, 600)
    baseline_camera = UsdGeom.Camera.Define(stage, '/FixtureExpectedCamera')
    baseline_camera.MakeMatrixXform().Set(expected)
    baseline_camera.GetHorizontalApertureAttr().Set(24)
    baseline_camera.GetVerticalApertureAttr().Set(18)
    baseline_camera.GetFocalLengthAttr().Set(24 / (2 * math.tan(math.radians(30))))
    baseline_camera.GetClippingRangeAttr().Set(Gf.Vec2f(.01 / units, 1000000 / units))
    viewport.camera_path = baseline_camera.GetPath()
    window.focus()
    baseline = await _capture(viewport, name + '-expected')
    _landmark_pixels(baseline)
    archive, identities = _archive(name, baseline.read_bytes(), axis)
    archive_bytes = archive.read_bytes()
    local_id, world_id = identities[0][1], identities[1][1]
    context = omni.usd.get_context()
    context.get_selection().set_selected_prim_paths([paths[0]], False)
    controller = controller_for(service)
    baseline_path = str(viewport.camera_path)
    root_before = stage.GetRootLayer().ExportToString()
    try:
        review = await _open_review(controller, archive)
        wrong = next(view for view in review.plan.document.viewpoints if view.id == local_id)
        assert not Gf.IsClose(Gf.Matrix4d(*wrong.camera['transform']), expected, 1e-5)
        await _correct(review, local_id, True)
        temporary = await _assert_preview(review, viewport, expected, landmarks, baseline, name + '-local-preview')
        assert stage.GetRootLayer().ExportToString() == root_before, '\n'.join(difflib.unified_diff(root_before.splitlines(), stage.GetRootLayer().ExportToString().splitlines()))
        assert context.get_selection().get_selected_prim_paths() == [paths[0]]
        assert all(UsdGeom.Imageable(stage.GetPrimAtPath(path)).ComputeVisibility() == UsdGeom.Tokens.inherited for path in paths)
        assert not service.list_issues()
        review.cancel()
        await frames(3)
        assert str(viewport.camera_path) == baseline_path
        assert not stage.GetPrimAtPath(temporary)
        assert controller._import_camera_preview is None and controller._import_preview_listener is None
        assert stage.GetRootLayer().ExportToString() == root_before, '\n'.join(difflib.unified_diff(root_before.splitlines(), stage.GetRootLayer().ExportToString().splitlines()))
        assert not service.list_issues()

        # Persist the compatible default first, then exercise correction on reimport.
        review = await _open_review(controller, archive)
        review._apply_clicked()
        await frames(3)
        assert review.applied and not review._error, review._error
        review.cancel()
        assert not Gf.IsClose(Gf.Matrix4d(*service.store.get_viewpoint(local_id).camera['transform']), expected, 1e-5)
        review = await _open_review(controller, archive)
        await _correct(review, local_id, True)
        await _correct(review, world_id, False)
        await _assert_preview(review, viewport, expected, landmarks, baseline, name + '-world-preview')
        review._apply_clicked()
        await frames(3)
        assert review.applied and not review._error, review._error
        assert str(viewport.camera_path) == baseline_path
        assert controller._import_camera_preview is None and controller._import_preview_listener is None
        options = dict(review.plan.viewpoint_options_signatures)
        review.cancel()
        issues = service.list_issues()
        assert len(issues) == 2
        for topic, view, comment in identities:
            record = service.store.get_viewpoint(view)
            assert Gf.IsClose(Gf.Matrix4d(*record.camera['transform']), expected, 1e-5)
            assert record.snapshot == baseline.read_bytes()
            issue = service.get_issue(topic)
            assert len(issue.comments) == 1 and issue.comments[0].id == comment
            assert len(service.store.list_viewpoints(topic)) == 1
        from issues_tag.bcf import read_bcf, plan_import, apply_import
        before_repeat = stage.GetRootLayer().ExportToString()
        repeated = apply_import(plan_import(read_bcf(archive), service.store, viewpoint_options=options), {}, service)
        assert repeated.created == 0 and repeated.updated == 0 and repeated.viewpoints_updated == 0
        assert stage.GetRootLayer().ExportToString() == before_repeat
        saved = ARTIFACTS / (name + '-parent.usda')
        stage.GetRootLayer().Export(str(saved))
        reopened = IssueStore(Usd.Stage.Open(str(saved)))
        for _, view, _ in identities:
            assert reopened.get_viewpoint(view) == service.store.get_viewpoint(view)
        assert source_path.read_bytes() == source_bytes and archive.read_bytes() == archive_bytes
        assert not any(str(prim.GetPath()).startswith('/IssuesImportPreview_') for prim in stage.Traverse())
        _phase('accepted', scenario=name, issues=len(issues), comments=2, viewpoints=2, source_unchanged=True)
    finally:
        controller._close_import_camera_preview()
        await frames(3)
        for dialog in controller._dialogs:
            dialog.destroy()
        await close_controller(controller)
    await frames(5)
    _assert_preview_log_clean()


async def test_bcf_camera_preview_and_corrected_import(service):
    await _scenario(service, 'rotated-metres-z-up')


async def test_bcf_camera_centimetres_y_up(service):
    await _scenario(service, 'rotated-centimetres-y-up', .01, 'Y')



async def test_bcf_camera_preview_releases_native_navigation(service):
    from types import SimpleNamespace
    from omni.kit.viewport.utility import get_active_viewport_window
    from pxr import UsdRender
    from issues_tag.import_camera_preview import ImportCameraPreview
    stage = service.stage
    source, _, expected, _ = _model(stage, 'native-navigation', 1, 'Z')
    source_bytes = source.read_bytes()
    viewport = get_active_viewport_window('Viewport').viewport_api
    viewport.resolution = (800, 600)
    original = UsdGeom.Camera.Define(stage, '/NavigationOriginal')
    original.MakeMatrixXform().Set(expected)
    original.GetHorizontalApertureAttr().Set(24)
    original.GetVerticalApertureAttr().Set(18)
    original.GetFocalLengthAttr().Set(24 / (2 * math.tan(math.radians(30))))
    viewport.camera_path = original.GetPath()
    baseline = await _capture(viewport, 'navigation-baseline')
    pixels = _landmark_pixels(baseline)
    original_product = str(viewport.render_product_path)
    product = UsdRender.Product(stage.GetPrimAtPath(original_product))
    session = stage.GetSessionLayer()
    with Usd.EditContext(stage, session):
        product.GetCameraRel().SetTargets([original.GetPath()])
    spec = session.GetRelationshipAtPath(product.GetCameraRel().GetPath())
    spec.targetPathList.ClearEdits()
    spec.targetPathList.prependedItems = [original.GetPath()]
    spec.targetPathList.deletedItems = [Sdf.Path('/UnrelatedDeletedCamera')]
    prior_targets = spec.GetInfo('targetPaths')
    before = stage.GetRootLayer().ExportToString()
    view = SimpleNamespace(camera=dict(projection='perspective',
        transform=[float(v) for row in expected for v in row], horizontal_aperture=24,
        vertical_aperture=18, focal_length=24 / (2 * math.tan(math.radians(30))), clipping_range=(.01, 10000)))
    preview = ImportCameraPreview(viewport, stage)
    try:
        preview.show(view)
        temporary = str(viewport.camera_path)
        artifact = await _capture(viewport, 'navigation-preview')
        assert str(viewport.camera_path) == temporary
        assert str(viewport.render_product_path) == original_product
        assert stage.GetRootLayer().ExportToString() == before
        for actual, expected_pixel in zip(_landmark_pixels(artifact), pixels):
            assert math.dist(actual, expected_pixel) < .025
        preview.close()
        await frames(5)
        assert str(viewport.camera_path) == str(original.GetPath())
        assert session.GetRelationshipAtPath(product.GetCameraRel().GetPath()).GetInfo('targetPaths') == prior_targets
        assert stage.GetRootLayer().ExportToString() == before
        assert not stage.GetPrimAtPath(temporary)

        with Usd.EditContext(stage, session):
            product.GetPrim().RemoveProperty('camera')
        new_owner = UsdGeom.Camera.Define(stage, '/NavigationNewOwner')
        for attr in original.GetPrim().GetAttributes():
            if attr.HasAuthoredValueOpinion():
                new_owner.GetPrim().CreateAttribute(attr.GetName(), attr.GetTypeName(), attr.IsCustom()).Set(attr.Get())
        shifted = Gf.Matrix4d(expected)
        shifted.SetTranslateOnly(expected.ExtractTranslation() + Gf.Vec3d(0, 1, 0))
        new_owner.MakeMatrixXform().Set(shifted)
        preview.show(view)
        temporary = str(viewport.camera_path)
        await _capture(viewport, 'navigation-second-preview')
        UsdGeom.Xform.Define(stage, '/UnrelatedUserEdit')
        viewport.camera_path = new_owner.GetPath()
        await frames(10)
        preview.close()
        artifact = await _capture(viewport, 'navigation-after-close')
        assert str(viewport.camera_path) == str(new_owner.GetPath())
        assert product.GetCameraRel().GetTargets() == [new_owner.GetPath()]
        assert math.dist(_landmark_pixels(artifact)[0], pixels[0]) > .03
        assert str(viewport.render_product_path) == original_product
        assert not stage.GetPrimAtPath(temporary)
        assert stage.GetRootLayer().GetPrimAtPath('/UnrelatedUserEdit')
        assert source.read_bytes() == source_bytes
        _phase('navigation_released', camera=str(viewport.camera_path), product=original_product,
               centroids=_landmark_pixels(artifact), previous_centroids=pixels)
    finally:
        preview.close()
    await frames(5)
    _assert_preview_log_clean()
