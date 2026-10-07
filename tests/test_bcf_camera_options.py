"""Explicit camera corrections against real BCF parsing and USD composition."""
from dataclasses import replace
import importlib
import io
import math
from pathlib import Path
import types
import unittest
from unittest.mock import patch
from uuid import uuid4
from xml.etree import ElementTree as ET

import test_bcf_compat as compatibility


class CameraOptionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compatibility.BcfCompatibilityTests.setUpClass()
        cls.api = compatibility.BcfCompatibilityTests.api
        cls.coordinates = importlib.import_module('_bcf_compat_product.bcf_coordinates')

    def setUp(self):
        self.fixture = compatibility.BcfCompatibilityTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.Usd, self.UsdGeom, self.Gf = self.fixture.usd()
        self.store_api = importlib.import_module('_bcf_compat_product.store')

    def document(self, *, position=(12, -4, 1), version='2.1', perspective=True):
        self.fixture.fixture()
        original = self.api.read_bcf(self.fixture.path)
        view = original.viewpoints[0]
        camera = 'PerspectiveCamera' if perspective else 'OrthogonalCamera'
        scale = '<FieldOfView>53.13010235415598</FieldOfView>' if perspective else '<ViewToWorldScale>5</ViewToWorldScale>'
        vectors = ''.join('<' + name + '>' + ''.join(f'<{axis}>{number}</{axis}>' for axis, number in zip('XYZ', values)) + '</' + name + '>' for name, values in (
            ('CameraViewPoint', position), ('CameraDirection', (0, 0, -1)), ('CameraUpVector', (0, 1, 0))))
        xml = ET.fromstring(f'<VisualizationInfo Guid="{view.id}"><{camera}>{vectors}{scale}<AspectRatio>{1502/891}</AspectRatio></{camera}><ClippingPlanes><ClippingPlane><Location><X>12</X><Y>0</Y><Z>0</Z></Location><Direction><X>1</X><Y>0</Y><Z>0</Z></Direction></ClippingPlane></ClippingPlanes></VisualizationInfo>')
        parsed = self.api._read_view(xml, view.snapshot, legacy=version == '2.1')
        return replace(original, viewpoints=(parsed,))

    def stage(self, *, units=1, axis='Z', rotated=False):
        from pxr import Sdf
        source = self.Usd.Stage.CreateNew(str(Path(self.fixture.directory.name) / 'source.usda'))
        self.UsdGeom.SetStageMetersPerUnit(source, units)
        self.UsdGeom.SetStageUpAxis(source, axis)
        root = self.UsdGeom.Xform.Define(source, '/Model')
        source.SetDefaultPrim(root.GetPrim())
        site = self.UsdGeom.Xform.Define(source, '/Model/Site')
        site.GetPrim().CreateAttribute('omni:hoops:metadata:TYPE', Sdf.ValueTypeNames.String).Set('IFCSITE')
        site.AddTranslateOp().Set((579400, 6633600, 100))
        source.GetRootLayer().Save()
        stage = self.Usd.Stage.CreateInMemory()
        self.UsdGeom.SetStageMetersPerUnit(stage, units)
        self.UsdGeom.SetStageUpAxis(stage, axis)
        for path in ('/World/A', '/World/B'):
            root = self.UsdGeom.Xform.Define(stage, path)
            root.GetPrim().GetReferences().AddReference(source.GetRootLayer().identifier)
            if path.endswith('B'):
                root.AddTranslateOp().Set((20, 30, 40))
            elif rotated:
                root.AddRotateZOp().Set(90)
        store = self.store_api.IssueStore(stage)
        service = types.SimpleNamespace(stage=stage, store=store, list_issues=store.list_issues, mutate=lambda operation: operation())
        return service

    def options(self, **kwargs):
        self.assertTrue(hasattr(self.coordinates, 'ViewpointImportOptions'), 'Explicit viewpoint import options are missing')
        return self.coordinates.ViewpointImportOptions(**kwargs)

    def plan(self, document, service, **kwargs):
        return self.api.plan_import(document, service.store, reference_path='/World/A/Site', **kwargs)

    def assert_position(self, view, expected):
        for actual, value in zip(view.camera['transform'][12:15], expected):
            self.assertAlmostEqual(actual, value, places=7)

    def test_world_default_and_explicit_local_map_position_and_planes(self):
        service = self.stage()
        document = self.document()
        identity = document.viewpoints[0].id
        self.assert_position(self.plan(document, service).document.viewpoints[0], (12, -4, 1))
        survey = self.document(position=(579412, 6633596, 101))
        self.assert_position(self.plan(survey, service).document.viewpoints[0], (579412, 6633596, 101))
        plan = self.plan(document, service, viewpoint_options={identity: self.options(coordinate_mode='reference_local')})
        converted = plan.document.viewpoints[0]
        self.assert_position(converted, (579412, 6633596, 101))
        self.assertEqual(converted.clipping_planes, ((1, 0, 0, -579412),))
        self.assertEqual(converted.coordinate_frame['bcf_coordinate_mode'], 'reference_local')
        self.assertEqual(converted.coordinate_frame['bcf_fov_mode'], 'file')
        self.assertEqual(plan.source_document, document)

    def test_rotated_parent_and_centimetre_y_up_local_frame(self):
        service = self.stage(units=.01, axis='Y', rotated=True)
        document = self.document()
        plan = self.plan(document, service, viewpoint_options={document.viewpoints[0].id: self.options(coordinate_mode='reference_local')})
        view = plan.document.viewpoints[0]
        # Z-up metres become (1200,100,400) in Y-up centimetres, then site and parent.
        self.assert_position(view, (-6633700, 580600, 500))
        self.assertAlmostEqual(view.clipping_planes[0][0], 0, places=7)
        self.assertAlmostEqual(view.clipping_planes[0][1], 1, places=7)
        self.assertAlmostEqual(view.clipping_planes[0][3], -580600, places=7)
        for actual, expected in zip(view.camera['clipping_range'], (1, 100000000)):
            self.assertAlmostEqual(actual / expected, 1, places=7)
        self.assertAlmostEqual(view.camera['transform'][8], -1, places=7)

    def test_horizontal_is_explicit_and_only_standard_21_perspective(self):
        service = self.stage()
        document = self.document()
        identity = document.viewpoints[0].id
        default = self.plan(document, service).document.viewpoints[0]
        horizontal = self.plan(document, service, viewpoint_options={identity: self.options(fov_mode='horizontal')}).document.viewpoints[0]
        def angle(view, key):
            return math.degrees(2 * math.atan(view.camera[key] / (2 * view.camera['focal_length'])))
        self.assertAlmostEqual(angle(default, 'vertical_aperture'), 53.13010235415598)
        self.assertAlmostEqual(angle(horizontal, 'horizontal_aperture'), 53.13010235415598)
        for invalid in (self.document(version='3.0'), self.document(perspective=False), replace(document, native_viewpoints=(identity,))):
            with self.subTest(native=invalid.native_viewpoints, source=invalid.viewpoints[0].coordinate_frame['bcf_source_camera']):
                with self.assertRaisesRegex(ValueError, 'horizontal.*2.1.*perspective'):
                    self.plan(invalid, service, viewpoint_options={invalid.viewpoints[0].id: self.options(fov_mode='horizontal')})

    def test_invalid_options_and_unresolved_local_frame_fail_without_mutation(self):
        service = self.stage()
        document = self.document()
        identity = document.viewpoints[0].id
        for kwargs in ({'coordinate_mode': 'guess'}, {'fov_mode': 'guess'}, {'reference_path': 3}):
            with self.assertRaises(ValueError):
                self.options(**kwargs)
        for opts in ({str(uuid4()): self.options()}, {identity: {'unknown': True}}, {identity: self.options(reference_path='/World/Missing', coordinate_mode='reference_local')}):
            with self.assertRaises(ValueError):
                self.plan(document, service, viewpoint_options=opts)
        empty = types.SimpleNamespace(store=self.store_api.IssueStore(self.Usd.Stage.CreateInMemory()))
        with self.assertRaisesRegex(ValueError, 'reference'):
            self.api.plan_import(document, empty.store, viewpoint_options={identity: self.options(coordinate_mode='reference_local')})
        self.assertFalse(service.list_issues())

    def test_nondefault_reference_motion_and_stage_replacement_reject_before_mutation(self):
        service = self.stage()
        document = self.document()
        first = document.viewpoints[0]
        second = replace(first, id=str(uuid4()))
        document = replace(document, viewpoints=(first, second), viewpoint_topics=((first.id, document.issues[0].id), (second.id, document.issues[0].id)))
        plan = self.plan(document, service, viewpoint_options={second.id: self.options(reference_path='/World/B/Site')})
        self.UsdGeom.Xformable(service.stage.GetPrimAtPath('/World/B')).GetOrderedXformOps()[0].Set((21, 30, 40))
        with self.assertRaisesRegex(ValueError, 'coordinate frame changed'):
            self.api.apply_import(plan, {}, service)
        self.assertFalse(service.list_issues())
        service.stage = self.Usd.Stage.CreateInMemory()
        with patch.object(self.coordinates, 'stage_mapping', side_effect=AssertionError('Replacement stage traversed')):
            with self.assertRaisesRegex(ValueError, 'scene changed'):
                self.api.apply_import(plan, {}, service)

    def test_correction_replanning_repeat_save_reopen_and_export_preserve_evidence(self):
        service = self.stage()
        document = self.document()
        identity = document.viewpoints[0].id
        first = self.plan(document, service)
        self.api.apply_import(first, {}, service)
        existing = service.store.get_viewpoint(identity)
        image = io.BytesIO()
        compatibility.Image.new('RGB', (37, 23), 'red').save(image, format='PNG')
        local_evidence = image.getvalue()
        service.store.put_viewpoint(replace(existing, snapshot=local_evidence), document.issues[0].id)
        projection = self.plan(first.source_document, service, viewpoint_options={identity: self.options(fov_mode='horizontal')})
        self.assertEqual(self.api.apply_import(projection, {}, service).viewpoints_updated, 1)
        self.assert_position(service.store.get_viewpoint(identity), (12, -4, 1))
        options = {identity: self.options(reference_path='/World/B/Site', coordinate_mode='reference_local', fov_mode='horizontal')}
        corrected = self.plan(first.source_document, service, viewpoint_options=options)
        summary = self.api.apply_import(corrected, {}, service)
        stored = service.store.get_viewpoint(identity)
        self.assert_position(stored, (579432, 6633626, 141))
        self.assertEqual(stored.snapshot, local_evidence)
        self.assertEqual((summary.created, summary.updated, summary.comments_added, summary.viewpoints_added, summary.viewpoints_updated), (0, 0, 0, 0, 1))
        repeated = self.api.apply_import(self.plan(corrected.source_document, service, viewpoint_options=options), {}, service)
        self.assertEqual(repeated.viewpoints_updated, 0)
        reverted = self.plan(corrected.document, service, viewpoint_options={identity: self.options(fov_mode='file')})
        self.api.apply_import(reverted, {}, service)
        self.assert_position(service.store.get_viewpoint(identity), (12, -4, 1))
        self.assertEqual(service.store.get_viewpoint(identity).camera, first.document.viewpoints[0].camera)
        parent = Path(self.fixture.directory.name) / 'parent.usda'
        service.stage.GetRootLayer().Export(str(parent))
        reopened = self.store_api.IssueStore(self.Usd.Stage.Open(str(parent)))
        self.assertEqual(reopened.get_viewpoint(identity), service.store.get_viewpoint(identity))
        exported = Path(self.fixture.directory.name) / 'export.bcf'
        self.api.write_bcf(self.api.export_document(reopened), exported)
        reread = self.api.read_bcf(exported)
        self.assertEqual(reread.viewpoints[0].camera, reopened.get_viewpoint(identity).camera)
        self.assertEqual(reread.viewpoints[0].snapshot, local_evidence)

    def test_editable_markup_blocks_atomic_frame_or_fov_correction(self):
        service = self.stage()
        document = self.document()
        self.api.apply_import(self.plan(document, service), {}, service)
        identity = document.viewpoints[0].id
        existing = service.store.get_viewpoint(identity)
        existing = replace(existing, markup_path='/Viewport_Markups/Edit')
        service.store.put_viewpoint(existing, document.issues[0].id)
        baseline = service.stage.GetRootLayer().ExportToString()
        for option in (self.options(fov_mode='horizontal'), self.options(coordinate_mode='reference_local')):
            with self.assertRaisesRegex(ValueError, 'editable Markup'):
                self.api.apply_import(self.plan(document, service, viewpoint_options={identity: option}), {}, service)
            self.assertEqual(service.stage.GetRootLayer().ExportToString(), baseline)
        self.assertEqual(self.api.apply_import(self.plan(document, service), {}, service).viewpoints_updated, 0)

    def test_malformed_ownership_is_rejected_by_planner_and_writer(self):
        service = self.stage()
        document = self.document()
        identity, topic = document.viewpoints[0].id, document.issues[0].id
        for ownership in (((identity, str(uuid4())),), ((str(uuid4()), topic),), ((identity, topic), (identity, topic))):
            invalid = replace(document, viewpoint_topics=ownership)
            with self.assertRaisesRegex(ValueError, 'ownership'):
                self.plan(invalid, service)
            with self.assertRaisesRegex(ValueError, 'ownership'):
                self.api.write_bcf(invalid, Path(self.fixture.directory.name) / 'invalid.bcf')
        other_topic = str(uuid4())
        other = replace(document.issues[0], id=other_topic, bcf_topic_id=other_topic, initial_viewpoint_id='', comments=())
        contradictory = replace(document, issues=(*document.issues, other), viewpoint_topics=((identity, other.id),))
        with self.assertRaisesRegex(ValueError, 'ownership'):
            self.api.write_bcf(contradictory, Path(self.fixture.directory.name) / 'contradictory.bcf')

    def test_native_editable_camera_and_explicit_native_reference_are_protected(self):
        service = self.stage()
        document = self.document()
        identity = document.viewpoints[0].id
        self.api.apply_import(self.plan(document, service), {}, service)
        stored = service.store.get_viewpoint(identity)
        frame = {key: value for key, value in stored.coordinate_frame.items() if not key.startswith('bcf_')}
        service.store.put_viewpoint(replace(stored, coordinate_frame=frame, markup_path='/Viewport_Markups/Native'), document.issues[0].id)
        before = service.stage.GetRootLayer().ExportToString()
        with self.assertRaisesRegex(ValueError, 'editable Markup'):
            self.api.apply_import(self.plan(document, service, viewpoint_options={identity: self.options(coordinate_mode='reference_local')}), {}, service)
        self.assertEqual(service.stage.GetRootLayer().ExportToString(), before)
        native = replace(document, native_viewpoints=(identity,))
        self.assertEqual(self.plan(native, service).document.viewpoints, native.viewpoints)
        with self.assertRaisesRegex(ValueError, 'Native'):
            self.plan(native, service, viewpoint_options={identity: self.options(reference_path='/World/A/Site')})

    def test_only_explicit_references_need_no_ambiguous_default_and_owned_views_import(self):
        service = self.stage()
        document = self.document()
        first = document.viewpoints[0]
        second = replace(first, id=str(uuid4()))
        document = replace(document, viewpoints=(first, second), viewpoint_topics=((first.id, document.issues[0].id), (second.id, document.issues[0].id)))
        options = {first.id: self.options(reference_path='/World/A/Site'), second.id: self.options(reference_path='/World/B/Site', coordinate_mode='reference_local')}
        plan = self.api.plan_import(document, service.store, viewpoint_options=options)
        summary = self.api.apply_import(plan, {}, service)
        self.assertEqual(summary.viewpoints_added, 2)
        self.assert_position(service.store.get_viewpoint(second.id), (579432, 6633626, 141))
        self.assertEqual(dict(plan.viewpoint_options_signatures), options)
        self.assertEqual(set(dict(plan.viewpoint_frame_signatures)), {first.id, second.id})
        corrections = {first.id: options[first.id], second.id: self.options(reference_path='/World/A/Site', coordinate_mode='reference_local', fov_mode='horizontal')}
        corrected = self.api.plan_import(plan.source_document, service.store, viewpoint_options=corrections)
        self.assertEqual(self.api.apply_import(corrected, {}, service).viewpoints_updated, 1)
        parent = Path(self.fixture.directory.name) / 'owned-parent.usda'
        service.stage.GetRootLayer().Export(str(parent))
        reopened = self.store_api.IssueStore(self.Usd.Stage.Open(str(parent)))
        topic = document.issues[0].id
        exported = Path(self.fixture.directory.name) / 'owned-export.bcf'
        self.api.write_bcf(self.api.export_document(reopened), exported)
        reread = self.api.read_bcf(exported)
        self.assertEqual(set(reread.viewpoint_topics), {(first.id, topic), (second.id, topic)})
        self.assertEqual({view.id for view in reread.viewpoints}, {first.id, second.id})
        self.assertEqual({view.id for view in reopened.list_viewpoints(topic)}, {first.id, second.id})
        saved = {view.id: view for view in reread.viewpoints}[second.id]
        self.assertEqual((saved.snapshot, saved.camera, saved.coordinate_frame), (second.snapshot, reopened.get_viewpoint(second.id).camera, reopened.get_viewpoint(second.id).coordinate_frame))

    def test_mapped_document_defaults_are_preserved_and_source_document_is_unconverted(self):
        service = self.stage()
        document = self.document()
        identity = document.viewpoints[0].id
        options = {identity: self.options(reference_path='/World/B/Site', coordinate_mode='reference_local', fov_mode='horizontal')}
        corrected = self.api.plan_import(document, service.store, viewpoint_options=options)
        preserved = self.api.plan_import(corrected.document, service.store)
        self.assertEqual(preserved.document, corrected.document)
        self.assertEqual(preserved.source_document, document)

    def test_local_mapping_rejects_nonuniform_scale_shear_and_reflection(self):
        service = self.stage()
        site = self.UsdGeom.Xformable(service.stage.GetPrimAtPath('/World/A/Site'))
        document = self.document()
        identity = document.viewpoints[0].id
        # Author a single matrix op so each invalid transform is independent.
        site.ClearXformOpOrder()
        matrix_op = site.AddTransformOp()
        for matrix in (self.Gf.Matrix4d().SetScale((1, 2, 1)), self.Gf.Matrix4d().SetScale((-1, 1, 1)), self.Gf.Matrix4d(1, .2, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)):
            matrix_op.Set(matrix)
            with self.assertRaisesRegex(ValueError, 'uniform scale'):
                self.plan(document, service, viewpoint_options={identity: self.options(coordinate_mode='reference_local')})
        self.assertFalse(service.list_issues())

    def test_reimport_updates_target_frame_metadata_when_mapping_matrix_is_unchanged(self):
        service = self.stage()
        document = self.document()
        self.api.apply_import(self.plan(document, service), {}, service)
        self.UsdGeom.SetStageMetersPerUnit(service.stage, .01)
        self.UsdGeom.SetStageUpAxis(service.stage, 'Y')
        summary = self.api.apply_import(self.plan(document, service), {}, service)
        self.assertEqual(summary.viewpoints_updated, 1)
        frame = service.store.get_viewpoint(document.viewpoints[0].id).coordinate_frame
        self.assertEqual((frame['meters_per_unit'], frame['up_axis']), (.01, 'Y'))


if __name__ == '__main__':
    unittest.main()
