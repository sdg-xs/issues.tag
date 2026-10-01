"""Offline routing tests; native camera/render behavior still needs Kit verification."""
import importlib.util
import sys
import types
import unittest
import os
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

try:
    from pxr import Gf, Usd, UsdGeom
except ImportError:
    usd = next((ROOT.parent / 'verification-dependencies' / 'extscache').glob('omni.usd.libs-*'))
    _dll_handles = [os.add_dll_directory(str(usd / 'bin'))]
    sys.path.insert(0, str(usd))
    from pxr import Gf, Usd, UsdGeom


def module(name, **values):
    result = types.ModuleType(name)
    result.__dict__.update(values)
    result.__path__ = []
    return result


class RecallTests(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.stage = Usd.Stage.CreateInMemory()
        self.context = types.SimpleNamespace(get_stage=lambda: self.stage)
        self.api = types.SimpleNamespace(stage=self.stage, camera_path='/IssuesReviewCamera_1')
        self.window = types.SimpleNamespace(visible=True, viewport_api=self.api)
        self.viewport = types.SimpleNamespace(viewport=self.api, restore=self.restore)
        self.manager = types.SimpleNamespace(is_extension_enabled=lambda name: False)
        app = types.SimpleNamespace(get_app=lambda: types.SimpleNamespace(get_extension_manager=lambda: self.manager))
        self.windows = [self.window]
        utility = module('omni.kit.viewport.utility', get_active_viewport_window=lambda name: self.window)
        omni = module('omni')
        kit = module('omni.kit', app=app)
        omni.kit = kit
        carb = module('carb', settings=module('carb.settings'))
        modules = {'omni': omni, 'omni.kit': kit, 'omni.kit.app': app,
                   'omni.kit.commands': module('omni.kit.commands'), 'omni.usd': module('omni.usd'),
                   'omni.kit.viewport': module('omni.kit.viewport'), 'omni.kit.viewport.utility': utility,
                   'omni.kit.viewport.window': module('omni.kit.viewport.window', get_viewport_window_instances=lambda context=None: self.windows),
                   'carb': carb, 'carb.settings': carb.settings,
                   '_recall_product': module('_recall_product'),
                   '_recall_product.commands': module('_recall_product.commands', UpdateIssuesCommand=object),
                   '_recall_product.store': module('_recall_product.store', IssueStore=lambda stage: self.store),
                   '_recall_product.viewport': module('_recall_product.viewport', ViewportAdapter=lambda service, api: self.viewport)}
        self.patches = patch.dict(sys.modules, modules)
        self.patches.start()
        self.addCleanup(self.patches.stop)
        loaded = {}
        for name in ('model', 'service', 'markup'):
            spec = importlib.util.spec_from_file_location('_recall_product.' + name, ROOT / 'issues_tag' / (name + '.py'))
            loaded[name] = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = loaded[name]
            spec.loader.exec_module(loaded[name])
        model = loaded['model']
        source = UsdGeom.Camera.Define(self.stage, '/SourceCamera')
        source.MakeMatrixXform().Set(Gf.Matrix4d().SetTranslate(Gf.Vec3d(2, 3, 4)))
        UsdGeom.Camera.Define(self.stage, '/OmniverseKit_Persp')
        values = {'projection': str(source.GetProjectionAttr().Get()), 'transform': [float(source.ComputeLocalToWorldTransform(Usd.TimeCode.Default())[r][c]) for r in range(4) for c in range(4)], 'horizontal_aperture': float(source.GetHorizontalApertureAttr().Get()), 'vertical_aperture': float(source.GetVerticalApertureAttr().Get()), 'focal_length': float(source.GetFocalLengthAttr().Get()), 'clipping_range': list(source.GetClippingRangeAttr().Get())}
        self.record = model.ViewpointRecord('saved-view', camera=values, markup_path='/Viewport_Markups/Evidence')
        self.issue = types.SimpleNamespace(initial_viewpoint_id=self.record.id)
        self.store = types.SimpleNamespace(get_viewpoint=lambda key: self.record, get_issue=lambda key: self.issue)
        prim = self.stage.DefinePrim(self.record.markup_path)
        camera_prim = self.stage.DefinePrim(self.record.markup_path + '/camera')
        for attr in source.GetPrim().GetAttributes():
            if attr.Get() is not None:
                camera_prim.CreateAttribute(attr.GetName(), attr.GetTypeName()).Set(attr.Get())
        self.native = types.SimpleNamespace(path=self.record.markup_path, usd_prim=prim, camera_prim=camera_prim, recall=self.recall)
        self.core = types.SimpleNamespace(current_markup=None, editing_markup=None, get_markup_from_prim_path=lambda path: self.native)
        self.service = loaded['service'].IssueService.__new__(loaded['service'].IssueService)
        self.service._context = self.context
        self.service.viewport = self.viewport
        self.service.generation = 1
        self.adapter = loaded['markup'].MarkupAdapter(self.service)
        self.adapter.core = self.core
        self.assertTrue(hasattr(self.adapter, 'restore_viewpoint'), 'Native saved-view recall is not implemented')

    def restore(self, record, *, restore_camera=True):
        if record.coordinate_frame.get('mismatch'):
            raise ValueError('Coordinate frame mismatch')
        self.events.append(('issue-context', restore_camera, record.id))
        if restore_camera:
            self.api.camera_path = '/IssuesReviewCamera_1'

    def recall(self, **kwargs):
        self.events.append(('native-camera', kwargs))
        self.api.camera_path = '/OmniverseKit_Persp'

    def test_select_existing_evidence_uses_native_camera_without_annotation(self):
        self.service.native_view_recaller = self.adapter.restore_viewpoint
        self.service.open_issue('issue')
        self.assertEqual(self.events[0], ('issue-context', False, self.record.id))
        self.assertEqual(self.events[1], ('native-camera', {'without_camera': False, 'disable_settings': ['info', 'Approve', 'thumbnail']}))
        self.assertEqual(self.api.camera_path, '/OmniverseKit_Persp')
        self.assertIsNone(self.core.current_markup)
        self.assertIsNone(self.core.editing_markup)
        self.assertFalse(self.adapter._busy)
        self.assertEqual(self.record.camera['transform'][12:15], [2, 3, 4])

    def test_plain_and_bcf_view_use_portable_fallback_without_native_creation(self):
        from dataclasses import replace
        plain = replace(self.record, markup_path='')
        self.service.native_view_recaller = self.adapter.restore_viewpoint
        self.service.restore_viewpoint(plain)
        self.assertEqual(self.events, [('issue-context', True, plain.id)])

    def test_foreign_markup_is_not_recalled(self):
        self.native.usd_prim = types.SimpleNamespace(GetStage=lambda: object())
        self.service.native_view_recaller = self.adapter.restore_viewpoint
        self.service.restore_viewpoint(self.record)
        self.assertEqual(self.events, [('issue-context', True, self.record.id)])

    def test_native_recall_rejects_coordinate_mismatch_before_changes(self):
        from dataclasses import replace
        record = replace(self.record, coordinate_frame={'mismatch': True})
        with self.assertRaises(ValueError):
            self.adapter.restore_viewpoint(record)
        self.assertEqual(self.events, [])

    def test_active_vendor_annotation_is_preserved(self):
        foreign = object()
        self.core.current_markup = self.core.editing_markup = foreign
        with self.assertRaises(ValueError):
            self.adapter.restore_viewpoint(self.record)
        self.assertIs(self.core.current_markup, foreign)
        self.assertIs(self.core.editing_markup, foreign)
        self.assertEqual(self.events, [])

    def test_unready_native_core_does_not_activate_or_capture(self):
        self.adapter.core = None
        self.service.native_view_recaller = self.adapter.restore_viewpoint
        self.service.restore_viewpoint(self.record)
        self.assertEqual(self.events, [('issue-context', True, self.record.id)])

    def test_shared_perspective_camera_falls_back_without_moving_other_viewport(self):
        other = types.SimpleNamespace(stage=self.stage, camera_path='/OmniverseKit_Persp')
        self.windows.append(types.SimpleNamespace(viewport_api=other))
        self.service.native_view_recaller = self.adapter.restore_viewpoint
        self.assertFalse(self.service.restore_viewpoint(self.record))
        self.assertEqual(self.events, [('issue-context', True, self.record.id)])
        self.assertEqual(other.camera_path, '/OmniverseKit_Persp')

    def test_native_local_pose_and_projection_mismatch_use_portable_world_view(self):
        from dataclasses import replace
        for field, value in [('transform', [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 20, 3, 4, 1]), ('projection', 'orthographic'), ('focal_length', 150)]:
            record = replace(self.record, camera=dict(self.record.camera, **{field: value}))
            self.events.clear()
            self.service.native_view_recaller = self.adapter.restore_viewpoint
            self.assertFalse(self.service.restore_viewpoint(record))
            self.assertEqual(self.events, [('issue-context', True, record.id)])

    def test_destroy_releases_remaining_resources_after_notice_failure(self):
        def fail_revoke():
            raise RuntimeError('Notice failed')
        self.service._notice = types.SimpleNamespace(Revoke=fail_revoke)
        self.service._stage_events = object()
        self.service._listeners = [object()]
        self.service.native_view_recaller = self.adapter.restore_viewpoint
        with self.assertRaises(Exception) as caught:
            self.service.destroy()
        self.assertIsInstance(caught.exception, ExceptionGroup, 'Cleanup must preserve individual failure causes')
        self.assertEqual(str(caught.exception.exceptions[0]), 'Notice failed')
        self.assertIsNone(self.service._notice)
        self.assertIsNone(self.service._stage_events)
        self.assertEqual(self.service._listeners, [])
        self.assertIsNone(self.service.native_view_recaller)
        self.assertIsNone(self.service._context)

    def test_sampled_destination_camera_uses_portable_view_even_when_defaults_match(self):
        camera = UsdGeom.Camera(self.stage.GetPrimAtPath('/OmniverseKit_Persp'))
        transform = camera.MakeMatrixXform()
        transform.Set(Gf.Matrix4d().SetTranslate(Gf.Vec3d(2, 3, 4)))
        transform.Set(Gf.Matrix4d().SetTranslate(Gf.Vec3d(20, 3, 4)), Usd.TimeCode(1))
        camera.GetFocalLengthAttr().Set(150, Usd.TimeCode(1))
        self.service.native_view_recaller = self.adapter.restore_viewpoint
        self.assertFalse(self.service.restore_viewpoint(self.record))
        self.assertEqual(self.events, [('issue-context', True, self.record.id)])
        self.assertEqual(camera.ComputeLocalToWorldTransform(Usd.TimeCode(1)).ExtractTranslation(), Gf.Vec3d(20, 3, 4))
        self.assertEqual(camera.GetFocalLengthAttr().Get(Usd.TimeCode(1)), 150)


if __name__ == '__main__':
    unittest.main()
