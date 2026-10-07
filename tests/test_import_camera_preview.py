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

    def native_viewport(self):
        from pxr import UsdRender
        stage = self.stage
        product = UsdRender.Product.Define(stage, '/Render/OriginalProduct')
        product.GetCameraRel().SetTargets(['/Original'])

        class NativeViewport:
            def __init__(self):
                self.stage = stage
                self.render_product_path = '/Render/OriginalProduct'
                self._camera_path = '/Original'
                self.fail_activation = False

            def set_render_product_path(self, path, **kwargs):
                self.render_product_path = path
                self._camera_path = str(UsdRender.Product(self.stage.GetPrimAtPath(path)).GetCameraRel().GetTargets()[0])
                return True

            @property
            def camera_path(self):
                return self._camera_path

            @camera_path.setter
            def camera_path(self, value):
                self._camera_path = str(value)
                UsdRender.Product(self.stage.GetPrimAtPath(self.render_product_path)).GetCameraRel().SetTargets([value])
                if self.fail_activation and str(value).startswith('/IssuesImportPreview_'):
                    raise RuntimeError('activation failed')

        self.viewport = NativeViewport()
        return product

    def test_native_preview_keeps_product_and_restores_exact_session_list_ops(self):
        from pxr import Sdf, Usd
        product = self.native_viewport()
        with Usd.EditContext(self.stage, self.stage.GetSessionLayer()):
            product.GetCameraRel().SetTargets(['/Original'])
        spec = self.stage.GetSessionLayer().GetRelationshipAtPath(product.GetCameraRel().GetPath())
        spec.targetPathList.ClearEdits()
        spec.targetPathList.prependedItems = [Sdf.Path('/Original')]
        spec.targetPathList.deletedItems = [Sdf.Path('/Hidden')]
        before = self.stage.GetSessionLayer().ExportToString()
        root = self.stage.GetRootLayer().ExportToString()
        preview = self.preview()
        preview.show(self.view)
        self.assertEqual(self.viewport.render_product_path, '/Render/OriginalProduct')
        self.assertEqual(product.GetCameraRel().GetTargets(), [Sdf.Path(self.viewport.camera_path)])
        self.assertEqual(self.stage.GetRootLayer().ExportToString(), root)
        self.assertIsNone(preview.close())
        preview.close()
        self.assertEqual(self.stage.GetRootLayer().ExportToString(), root)
        self.assertEqual(self.stage.GetSessionLayer().ExportToString(), before)

    def test_exposure_schemas_and_values_are_session_only_and_pose_stays_imported(self):
        from pxr import Sdf
        self.native_viewport()
        original = self.stage.GetPrimAtPath('/Original')
        original.SetMetadata('apiSchemas', Sdf.TokenListOp.CreateExplicit(['OmniRtxCameraExposureAPI_1', 'OmniRtxCameraAutoExposureAPI_1', 'UnrelatedAPI']))
        original.CreateAttribute('exposure:fStop', Sdf.ValueTypeNames.Float).Set(7)
        original.CreateAttribute('omni:rtx:autoExposure:enabled', Sdf.ValueTypeNames.Bool).Set(True)
        original.CreateAttribute('omni:rtx:unrelated', Sdf.ValueTypeNames.Bool).Set(True)
        self.UsdGeom.Camera(original).GetFocalLengthAttr().Set(17)
        preview = self.preview()
        preview.show(self.view)
        camera = self.UsdGeom.Camera(self.stage.GetPrimAtPath(self.viewport.camera_path))
        schemas = camera.GetPrim().GetMetadata('apiSchemas')
        self.assertIsNotNone(schemas)
        self.assertEqual(schemas.ApplyOperations([]), ['OmniRtxCameraExposureAPI_1', 'OmniRtxCameraAutoExposureAPI_1'])
        self.assertEqual(camera.GetPrim().GetAttribute('exposure:fStop').Get(), 7)
        self.assertTrue(camera.GetPrim().GetAttribute('omni:rtx:autoExposure:enabled').Get())
        self.assertFalse(camera.GetPrim().GetAttribute('omni:rtx:unrelated'))
        self.assertAlmostEqual(camera.GetFocalLengthAttr().Get(), self.view.camera['focal_length'], places=4)
        preview.close()

    def test_independent_navigation_is_not_shadowed_by_preview_session_opinion(self):
        from pxr import Sdf, Usd
        product = self.native_viewport()
        self.UsdGeom.Camera.Define(self.stage, '/NewOwner')
        preview = self.preview()
        preview.show(self.view)
        temporary = self.viewport.camera_path
        with Usd.EditContext(self.stage, self.stage.GetSessionLayer()):
            product.GetPrim().CreateAttribute('keep', Sdf.ValueTypeNames.Bool).Set(True)
        self.viewport.camera_path = '/NewOwner'
        root = self.stage.GetRootLayer().ExportToString()
        preview.close()
        self.assertEqual(self.viewport.camera_path, '/NewOwner')
        self.assertEqual(product.GetCameraRel().GetTargets(), [Sdf.Path('/NewOwner')])
        self.assertEqual(self.stage.GetRootLayer().ExportToString(), root)
        self.assertTrue(product.GetPrim().GetAttribute('keep').Get())
        self.assertFalse(self.stage.GetPrimAtPath(temporary))

    def test_independent_session_relationship_edit_survives_close(self):
        from pxr import Sdf, Usd
        product = self.native_viewport()
        self.UsdGeom.Camera.Define(self.stage, '/NewOwner')
        preview = self.preview()
        preview.show(self.view)
        with Usd.EditContext(self.stage, self.stage.GetSessionLayer()):
            self.viewport.camera_path = '/NewOwner'
        preview.close()
        self.assertEqual(product.GetCameraRel().GetTargets(), [Sdf.Path('/NewOwner')])

    def test_direct_relationship_edit_survives_with_stale_viewport_cache(self):
        from pxr import Sdf, Usd
        product = self.native_viewport()
        self.UsdGeom.Camera.Define(self.stage, '/NewOwner')
        root = self.stage.GetRootLayer().ExportToString()
        preview = self.preview()
        preview.show(self.view)
        temporary = self.viewport.camera_path
        with Usd.EditContext(self.stage, self.stage.GetSessionLayer()):
            product.GetCameraRel().SetTargets(['/NewOwner'])
        self.assertEqual(self.viewport.camera_path, temporary)
        preview.close()
        self.assertEqual(product.GetCameraRel().GetTargets(), [Sdf.Path('/NewOwner')])
        self.assertEqual(self.viewport.camera_path, temporary)
        self.assertEqual(self.stage.GetRootLayer().ExportToString(), root)
        self.assertFalse(self.stage.GetPrimAtPath(temporary))

    def _assert_relationship_metadata_survives(self, prior):
        from pxr import Sdf, Usd
        product = self.native_viewport()
        relationship = product.GetCameraRel()
        session = self.stage.GetSessionLayer()
        if prior:
            with Usd.EditContext(self.stage, session):
                relationship.SetDocumentation('Prior documentation')
                if prior == 'targets':
                    relationship.SetTargets(['/Original'])
            if prior == 'targets':
                spec = session.GetRelationshipAtPath(relationship.GetPath())
                spec.targetPathList.ClearEdits()
                spec.targetPathList.prependedItems = [Sdf.Path('/Original')]
                spec.targetPathList.deletedItems = [Sdf.Path('/UnrelatedDeletedCamera')]
        before = session.GetRelationshipAtPath(relationship.GetPath())
        prior_targets = before.GetInfo('targetPaths') if before and before.HasInfo('targetPaths') else None
        root = self.stage.GetRootLayer().ExportToString()
        preview = self.preview()
        preview.show(self.view)
        with Usd.EditContext(self.stage, session):
            relationship.SetDocumentation('Independent documentation')
            relationship.SetCustomDataByKey('independent', 'keep')
        preview.close()
        self.assertEqual(relationship.GetDocumentation(), 'Independent documentation')
        self.assertEqual(relationship.GetCustomDataByKey('independent'), 'keep')
        after = session.GetRelationshipAtPath(relationship.GetPath())
        self.assertTrue(after)
        self.assertEqual(after.GetInfo('targetPaths') if after.HasInfo('targetPaths') else None, prior_targets)
        self.assertEqual(relationship.GetTargets(), [Sdf.Path('/Original')])
        self.assertEqual(self.stage.GetRootLayer().ExportToString(), root)

    def test_metadata_edit_survives_restoring_prior_target_list_ops(self):
        self._assert_relationship_metadata_survives('targets')

    def test_metadata_edit_survives_clearing_new_target_opinion_on_existing_relationship(self):
        self._assert_relationship_metadata_survives('metadata')

    def test_metadata_edit_survives_cleanup_of_new_session_relationship(self):
        self._assert_relationship_metadata_survives(None)

    def test_partial_activation_failure_restores_session_and_root(self):
        self.native_viewport()
        before = self.stage.GetSessionLayer().ExportToString()
        root = self.stage.GetRootLayer().ExportToString()
        self.viewport.fail_activation = True
        with self.assertRaisesRegex(RuntimeError, 'activation failed'):
            self.preview().show(self.view)
        self.assertEqual(self.viewport.camera_path, '/Original')
        self.assertEqual(self.stage.GetRootLayer().ExportToString(), root)
        self.assertEqual(self.stage.GetSessionLayer().ExportToString(), before)

    def test_native_replaced_stage_cleans_old_session_without_stale_restore(self):
        self.native_viewport()
        before = self.stage.GetSessionLayer().ExportToString()
        preview = self.preview()
        preview.show(self.view)
        replacement = self.fixture.Usd.Stage.CreateInMemory()
        self.viewport.stage = replacement
        self.viewport._camera_path = '/NewSceneCamera'
        preview.close()
        self.assertEqual(self.viewport.camera_path, '/NewSceneCamera')
        self.assertEqual(self.stage.GetSessionLayer().ExportToString(), before)

    def test_navigation_overrides_prior_camera_binding_but_keeps_its_metadata(self):
        from pxr import Sdf, Usd
        product = self.native_viewport()
        self.UsdGeom.Camera.Define(self.stage, '/NewOwner')
        with Usd.EditContext(self.stage, self.stage.GetSessionLayer()):
            product.GetCameraRel().SetTargets(['/Original'])
            product.GetCameraRel().SetDocumentation('Keep camera documentation')
        preview = self.preview()
        preview.show(self.view)
        self.viewport.camera_path = '/NewOwner'
        preview.close()
        self.assertEqual(product.GetCameraRel().GetTargets(), [Sdf.Path('/NewOwner')])
        self.assertEqual(product.GetCameraRel().GetDocumentation(), 'Keep camera documentation')

    def test_independently_selected_product_is_preserved(self):
        from pxr import Sdf, UsdRender
        product = self.native_viewport()
        self.UsdGeom.Camera.Define(self.stage, '/NewOwner')
        other = UsdRender.Product.Define(self.stage, '/Render/OtherProduct')
        other.GetCameraRel().SetTargets(['/NewOwner'])
        preview = self.preview()
        preview.show(self.view)
        temporary = self.viewport.camera_path
        self.viewport.set_render_product_path('/Render/OtherProduct')
        root = self.stage.GetRootLayer().ExportToString()
        preview.close()
        self.assertEqual(self.viewport.render_product_path, '/Render/OtherProduct')
        self.assertEqual(self.viewport.camera_path, '/NewOwner')
        self.assertEqual(product.GetCameraRel().GetTargets(), [Sdf.Path('/Original')])
        self.assertEqual(self.stage.GetRootLayer().ExportToString(), root)
        self.assertFalse(self.stage.GetPrimAtPath(temporary))


if __name__ == '__main__':
    unittest.main()
