"""Portable recall reuses the primary perspective camera without changing saved USD."""
import os
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
try:
    from pxr import Gf, Sdf, Usd, UsdGeom
except ImportError:
    libraries = next((Path.home() / '.codex/worktrees/issues-tag-improvements/verification-dependencies/extscache').glob('omni.usd.libs-*'))
    _dll_handle = os.add_dll_directory(str(libraries / 'bin'))
    sys.path.insert(0, str(libraries))
    from pxr import Gf, Sdf, Usd, UsdGeom
from test_lifecycle import lifecycle_sdk


class ReviewCameraTests(unittest.TestCase):
    def fixture(self, sdk):
        module = sdk.viewport
        module.Gf, module.Sdf, module.Usd, module.UsdGeom = Gf, Sdf, Usd, UsdGeom
        stage = Usd.Stage.CreateInMemory()
        camera = UsdGeom.Camera.Define(stage, '/OmniverseKit_Persp')
        camera.MakeMatrixXform().Set(Gf.Matrix4d(1))
        camera.GetPrim().CreateAttribute('omni:kit:cameraLock', Sdf.ValueTypeNames.Bool).Set(True)
        viewport = SimpleNamespace(stage=stage, camera_path='/OmniverseKit_Persp', render_product_path='/RenderProduct')
        primary = SimpleNamespace(viewport_api=viewport)
        module.vp_util.get_active_viewport_window = lambda name: primary
        module.vp_util.get_active_viewport = lambda **kw: viewport
        windows = types.ModuleType('omni.kit.viewport.window')
        windows.get_viewport_window_instances = lambda name: [primary]
        self.addCleanup(patch.stopall)
        patch.dict(sys.modules, {'omni.kit.viewport.window': windows}).start()
        service = SimpleNamespace(stage=stage, _context=SimpleNamespace(get_selection=lambda: SimpleNamespace(set_selected_prim_paths=lambda *args: None)))
        adapter = module.ViewportAdapter(service, viewport)
        pose = Gf.Matrix4d().SetTranslate(Gf.Vec3d(3, 4, 12))
        record = SimpleNamespace(coordinate_frame={}, camera={'projection': 'perspective',
            'transform': module.flatten(pose), 'horizontal_aperture': 20., 'vertical_aperture': 15.,
            'focal_length': 37., 'clipping_range': [.1, 1000.]}, section_state={}, visibility=(), selection=(), clipping_planes=())
        return stage, camera, viewport, adapter, record, windows, pose

    def test_primary_recall_reuses_camera_and_preserves_saved_scene(self):
        with lifecycle_sdk() as sdk:
            stage, camera, viewport, adapter, record, _, pose = self.fixture(sdk)
            before = stage.GetRootLayer().ExportToString()
            adapter.restore(record)
            self.assertEqual(viewport.camera_path, '/OmniverseKit_Persp')
            self.assertTrue(Gf.IsClose(camera.GetLocalTransformation(), pose, 1e-6))
            self.assertEqual(camera.GetFocalLengthAttr().Get(), 37.)
            self.assertFalse(camera.GetPrim().GetAttribute('omni:kit:cameraLock').Get())
            self.assertFalse(any(p.GetName().startswith('IssuesReviewCamera_') for p in stage.Traverse()))
            self.assertEqual(stage.GetRootLayer().ExportToString(), before)
            adapter.restore(record)
            self.assertFalse(any(p.GetName().startswith('IssuesReviewCamera_') for p in stage.Traverse()))

    def test_shared_perspective_camera_keeps_other_viewport_unchanged(self):
        with lifecycle_sdk() as sdk:
            stage, camera, viewport, adapter, record, windows, _ = self.fixture(sdk)
            other = SimpleNamespace(viewport_api=SimpleNamespace(stage=stage, camera_path='/OmniverseKit_Persp'))
            primary = SimpleNamespace(viewport_api=viewport)
            windows.get_viewport_window_instances = lambda name: [primary, other]
            before = camera.GetLocalTransformation()
            adapter.restore(record)
            self.assertTrue(viewport.camera_path.startswith('/IssuesReviewCamera_'))
            self.assertEqual(camera.GetLocalTransformation(), before)

    def test_centered_view_clears_previous_lens_shift_in_session_only(self):
        with lifecycle_sdk() as sdk:
            stage, camera, viewport, adapter, record, _, _ = self.fixture(sdk)
            camera.GetHorizontalApertureOffsetAttr().Set(8.)
            camera.GetVerticalApertureOffsetAttr().Set(-3.)
            before = stage.GetRootLayer().ExportToString()
            adapter.restore(record)
            self.assertEqual(viewport.camera_path, '/OmniverseKit_Persp')
            self.assertEqual(camera.GetHorizontalApertureOffsetAttr().Get(), 0.)
            self.assertEqual(camera.GetVerticalApertureOffsetAttr().Get(), 0.)
            self.assertEqual(stage.GetRootLayer().ExportToString(), before)

    def test_animated_perspective_camera_keeps_existing_samples(self):
        with lifecycle_sdk() as sdk:
            stage, camera, viewport, adapter, record, _, _ = self.fixture(sdk)
            camera.GetFocalLengthAttr().Set(80., 10)
            adapter.restore(record)
            self.assertTrue(viewport.camera_path.startswith('/IssuesReviewCamera_'))
            self.assertEqual(camera.GetFocalLengthAttr().Get(10), 80.)

    def test_imported_orthographic_recall_enables_orbit_in_session_only(self):
        with lifecycle_sdk() as sdk:
            stage, camera, viewport, adapter, record, _, _ = self.fixture(sdk)
            record.camera['projection'] = 'orthographic'
            camera.GetPrim().CreateAttribute('omni:kit:orthoRotate', Sdf.ValueTypeNames.Bool).Set(False)
            before = stage.GetRootLayer().ExportToString()
            adapter.restore(record)
            self.assertEqual(camera.GetProjectionAttr().Get(), 'orthographic')
            self.assertIs(camera.GetPrim().GetAttribute('omni:kit:orthoRotate').Get(), True)
            self.assertEqual(stage.GetRootLayer().ExportToString(), before)
            self.assertEqual(record.camera['projection'], 'orthographic')

    def test_shared_orthographic_recall_enables_only_the_review_camera(self):
        with lifecycle_sdk() as sdk:
            stage, camera, viewport, adapter, record, windows, _ = self.fixture(sdk)
            record.camera['projection'] = 'orthographic'
            camera.GetPrim().CreateAttribute('omni:kit:orthoRotate', Sdf.ValueTypeNames.Bool).Set(False)
            other = SimpleNamespace(viewport_api=SimpleNamespace(stage=stage, camera_path='/OmniverseKit_Persp'))
            windows.get_viewport_window_instances = lambda name: [SimpleNamespace(viewport_api=viewport), other]
            adapter.restore(record)
            review = stage.GetPrimAtPath(viewport.camera_path)
            self.assertIs(review.GetAttribute('omni:kit:orthoRotate').Get(), True)
            self.assertIs(camera.GetPrim().GetAttribute('omni:kit:orthoRotate').Get(), False)


if __name__ == '__main__':
    unittest.main()
