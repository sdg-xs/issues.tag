"""Real USD preview isolation with a viewport boundary double."""
import importlib
import unittest
from dataclasses import replace
from types import SimpleNamespace

import test_bcf_camera_options as camera_tests


class ImportCameraPreviewTests(unittest.TestCase):
    def setUp(self):
        camera_tests.CameraOptionsTests.setUpClass()
        self.fixture = camera_tests.CameraOptionsTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.stage = self.fixture.stage().stage
        self.UsdGeom, self.Gf = self.fixture.UsdGeom, self.fixture.Gf
        self.UsdGeom.Camera.Define(self.stage, '/Original')
        self.viewport = SimpleNamespace(stage=self.stage, camera_path='/Original', selection=['/World'])
        self.document = self.fixture.document()
        self.store = self.fixture.store_api.IssueStore(self.stage)
        self.view = self.fixture.api.plan_import(self.document, self.store, reference_path='/World/A/Site').document.viewpoints[0]

    def preview(self):
        name = '_bcf_compat_product.import_camera_preview'
        self.assertIsNotNone(importlib.util.find_spec(name), 'Camera-only import preview is missing')
        return importlib.import_module(name).ImportCameraPreview(self.viewport, self.stage)

    def test_only_temporary_camera_changes_and_close_restores_owned_camera(self):
        from pxr import Sdf, Usd
        with Usd.EditContext(self.stage, self.stage.GetSessionLayer()):
            self.UsdGeom.Xform.Define(self.stage, '/KeepSession')
            render = self.stage.DefinePrim('/Render')
            render.CreateAttribute('omni:rtx:scene:sectionPlane:enabled', Sdf.ValueTypeNames.Bool).Set(True)
        layers = {layer.identifier: layer.ExportToString() for layer in self.stage.GetUsedLayers()}
        target = self.stage.GetEditTarget()
        preview = self.preview()
        preview.show(self.view)
        temporary = str(self.viewport.camera_path)
        self.assertNotEqual(temporary, '/Original')
        camera = self.UsdGeom.Camera(self.stage.GetPrimAtPath(temporary))
        self.assertTrue(camera)
        self.assertEqual(tuple(camera.ComputeLocalToWorldTransform(Usd.TimeCode.Default()).ExtractTranslation()), tuple(self.view.camera['transform'][12:15]))
        self.assertEqual(self.stage.GetEditTarget(), target)
        self.assertEqual(self.viewport.selection, ['/World'])
        self.assertTrue(render.GetAttribute('omni:rtx:scene:sectionPlane:enabled').Get())
        for layer in self.stage.GetUsedLayers():
            if layer != self.stage.GetSessionLayer():
                self.assertEqual(layer.ExportToString(), layers[layer.identifier])
        with Usd.EditContext(self.stage, self.stage.GetSessionLayer()):
            self.UsdGeom.Xform.Define(self.stage, '/AddedDuringPreview')
        preview.close()
        preview.close()
        self.assertEqual(str(self.viewport.camera_path), '/Original')
        self.assertFalse(self.stage.GetPrimAtPath(temporary))
        self.assertTrue(self.stage.GetPrimAtPath('/AddedDuringPreview'))
        self.assertTrue(self.stage.GetPrimAtPath('/KeepSession'))
        self.assertFalse(self.store.list_issues())

    def test_newer_camera_owner_is_preserved_and_next_preview_restores_it(self):
        preview = self.preview()
        preview.show(self.view)
        old = str(self.viewport.camera_path)
        self.UsdGeom.Camera.Define(self.stage, '/NewOwner')
        self.viewport.camera_path = '/NewOwner'
        preview.show(self.view)
        preview.close()
        self.assertEqual(str(self.viewport.camera_path), '/NewOwner')
        self.assertFalse(self.stage.GetPrimAtPath(old))

    def test_stage_replacement_never_restores_camera_on_new_stage(self):
        preview = self.preview()
        preview.show(self.view)
        temporary = str(self.viewport.camera_path)
        self.viewport.stage = self.fixture.Usd.Stage.CreateInMemory()
        self.viewport.camera_path = '/Replacement'
        before = self.viewport.stage.GetSessionLayer().ExportToString()
        preview.close()
        self.assertEqual(self.viewport.camera_path, '/Replacement')
        self.assertEqual(self.viewport.stage.GetSessionLayer().ExportToString(), before)
        self.assertFalse(self.stage.GetPrimAtPath(temporary))
        with self.assertRaisesRegex(ValueError, 'scene'):
            preview.show(self.view)

    def test_missing_camera_leaves_stage_and_viewport_unchanged(self):
        preview = self.preview()
        before = self.stage.GetSessionLayer().ExportToString()
        with self.assertRaisesRegex(ValueError, 'camera'):
            preview.show(replace(self.view, camera={}))
        self.assertEqual(self.stage.GetSessionLayer().ExportToString(), before)
        self.assertEqual(self.viewport.camera_path, '/Original')


if __name__ == '__main__':
    unittest.main()
