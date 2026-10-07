"""Offline BCF checks; no Kit app runs, and saved user scenes are read-only."""
import importlib
import io
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from uuid import uuid4
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
TEST_PACKAGES = Path.home() / '.codex/worktrees/issues-tag-improvements/issues.tag/verification/python'
if TEST_PACKAGES.is_dir():
    sys.path.insert(0, str(TEST_PACKAGES))
from PIL import Image


class BcfCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        package = types.ModuleType('_bcf_compat_product')
        package.__path__ = [str(ROOT / 'issues_tag')]
        sys.modules[package.__name__] = package
        cls.api = importlib.import_module(package.__name__ + '.bcf')

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'sample.bcf'

    def fixture(self, *, camera=True, status='open', author='', version='2.1', ref=None):
        topic, view, comment = (str(uuid4()) for _ in range(3))
        image = io.BytesIO()
        Image.new('RGB', (300, 200)).save(image, format='JPEG')
        vectors = '<CameraViewPoint><X>1</X><Y>2</Y><Z>3</Z></CameraViewPoint><CameraDirection><X>0</X><Y>0</Y><Z>-1</Z></CameraDirection><CameraUpVector><X>0</X><Y>1</Y><Z>0</Z></CameraUpVector>'
        visual = f'<VisualizationInfo Guid="{view}">' + (f'<OrthogonalCamera>{vectors}<ViewToWorldScale>5</ViewToWorldScale></OrthogonalCamera>' if camera else '') + '</VisualizationInfo>'
        markup = f'<Markup><Topic Guid="{topic}" TopicType="Issue" TopicStatus="{status}"><Title>Opening</Title><Description>Check clearance</Description><CreationDate>2026-02-23T10:46:22.130</CreationDate><CreationAuthor>Reviewer</CreationAuthor></Topic><Comment Guid="{comment}"><Date>2026-02-24T10:00:00</Date><Author>{author}</Author><Comment>Check this</Comment><Viewpoint Guid="{view}"/></Comment><Viewpoints Guid="{view}"><Viewpoint>{ref or "view.bcfv"}</Viewpoint><Snapshot>snapshot.png</Snapshot></Viewpoints></Markup>'
        with ZipFile(self.path, 'w') as archive:
            archive.writestr('bcf.version', f'<Version VersionId="{version}"/>')
            archive.writestr(topic + '/markup.bcf', markup)
            archive.writestr(topic + '/view.bcfv', visual)
            archive.writestr(topic + '/snapshot.png', image.getvalue())
        return topic, view

    def test_21_layout_status_dates_comments_and_snapshot_aspect(self):
        topic, view = self.fixture()
        document = self.api.read_bcf(self.path)
        issue, viewpoint = document.issues[0], document.viewpoints[0]
        self.assertEqual(issue.id, topic)
        self.assertEqual(issue.status.value, 'Open')
        self.assertEqual(issue.initial_viewpoint_id, view)
        self.assertEqual(issue.comments[0].viewpoint_id, view)
        self.assertEqual(issue.comments[0].author, 'Unknown author')
        self.assertTrue(issue.created_at.endswith('+00:00'))
        self.assertEqual(viewpoint.camera['horizontal_aperture'] / viewpoint.camera['vertical_aperture'], 1.5)
        self.assertTrue(viewpoint.snapshot.startswith(b'\xff\xd8'))
        self.assertTrue(any('timezone' in warning for warning in document.warnings))

    def test_snapshot_only_view_survives_30_round_trip(self):
        self.fixture(camera=False)
        document = self.api.read_bcf(self.path)
        self.assertFalse(document.viewpoints[0].camera)
        self.assertFalse(document.issues[0].initial_viewpoint_id)
        exported = Path(self.directory.name) / 'export.bcf'
        self.api.write_bcf(document, exported)
        reread = self.api.read_bcf(exported)
        self.assertEqual(reread.issues, document.issues)
        self.assertEqual(reread.viewpoints[0].snapshot, document.viewpoints[0].snapshot)

    def test_unknown_status_is_not_silently_mapped(self):
        self.fixture(status='something else')
        with self.assertRaisesRegex(ValueError, 'unsupported status'):
            self.api.read_bcf(self.path)

    def test_30_still_requires_extensions_and_timezone(self):
        self.fixture(version='3.0')
        with self.assertRaisesRegex(ValueError, 'extensions.xml'):
            self.api.read_bcf(self.path)
        with self.assertRaisesRegex(ValueError, 'timezone'):
            self.api._import_date('2026-02-23T10:46:22', False, [])

    def test_21_cannot_follow_unsafe_viewpoint_paths(self):
        self.fixture(ref='../view.bcfv')
        with self.assertRaisesRegex(ValueError, 'unsafe path'):
            self.api.read_bcf(self.path)

    def test_supplied_archive_and_30_export_keep_all_records(self):
        sample = Path(os.environ.get('ISSUES_BCF_SAMPLE', str(Path.home() / 'Downloads/2026-09-30 11_36 106 Issues.bcf')))
        if not sample.is_file():
            self.skipTest('Set ISSUES_BCF_SAMPLE to the supplied 106-issue archive')
        document = self.api.read_bcf(sample)
        self.assertEqual(len(document.issues), 106)
        self.assertEqual(sum(len(issue.comments) for issue in document.issues), 118)
        self.assertEqual(len(document.viewpoints), 121)
        self.assertEqual(sum(bool(view.camera) for view in document.viewpoints), 108)
        exported = Path(self.directory.name) / 'sample-export.bcf'
        self.api.write_bcf(document, exported)
        reread = self.api.read_bcf(exported)
        self.assertEqual(reread.issues, document.issues)
        self.assertEqual({view.id: view.snapshot for view in reread.viewpoints}, {view.id: view.snapshot for view in document.viewpoints})

    def test_supplied_archive_import_save_reopen_and_repeat(self):
        sample = Path(os.environ.get('ISSUES_BCF_SAMPLE', str(Path.home() / 'Downloads/2026-09-30 11_36 106 Issues.bcf')))
        if not sample.is_file():
            self.skipTest('Set ISSUES_BCF_SAMPLE to the supplied 106-issue archive')
        try:
            from pxr import Usd
        except ImportError:
            dependencies = Path.home() / '.codex/worktrees/issues-tag-improvements/verification-dependencies/extscache'
            libraries = list(dependencies.glob('omni.usd.libs-*'))
            if not libraries:
                self.skipTest('Standalone USD libraries are unavailable')
            handle = os.add_dll_directory(str(libraries[0] / 'bin'))
            self.addCleanup(handle.close)
            sys.path.insert(0, str(libraries[0]))
            from pxr import Usd
        store_api = importlib.import_module('_bcf_compat_product.store')
        stage = Usd.Stage.CreateInMemory()
        service = types.SimpleNamespace(stage=stage, store=store_api.IssueStore(stage))
        service.list_issues = lambda: service.store.list_issues()
        service.mutate = lambda operation: operation()
        document = self.api.read_bcf(sample)
        plan = self.api.plan_import(document, service.store)
        summary = self.api.apply_import(plan, {}, service)
        self.assertEqual((summary.created, summary.comments_added, summary.viewpoints_added), (106, 118, 121))
        parent = Path(self.directory.name) / 'import-parent.usda'
        stage.GetRootLayer().Export(str(parent))
        service.stage = Usd.Stage.Open(str(parent))
        service.store = store_api.IssueStore(service.stage)
        self.assertEqual(len(service.list_issues()), 106)
        for viewpoint in plan.document.viewpoints:
            self.assertEqual(service.store.get_viewpoint(viewpoint.id), viewpoint)
        repeated = self.api.apply_import(self.api.plan_import(document, service.store), {}, service)
        self.assertEqual((repeated.created, repeated.updated, repeated.comments_added, repeated.viewpoints_added), (0, 0, 0, 0))

    def usd(self):
        try:
            from pxr import Usd, UsdGeom, Gf
        except ImportError:
            dependencies = Path.home() / '.codex/worktrees/issues-tag-improvements/verification-dependencies/extscache'
            libraries = list(dependencies.glob('omni.usd.libs-*'))
            if not libraries:
                self.skipTest('Standalone USD libraries are unavailable')
            handle = os.add_dll_directory(str(libraries[0] / 'bin'))
            self.addCleanup(handle.close)
            sys.path.insert(0, str(libraries[0]))
            from pxr import Usd, UsdGeom, Gf
        return Usd, UsdGeom, Gf

    def reference_stage(self):
        Usd, UsdGeom, Gf = self.usd()
        source = Usd.Stage.CreateNew(str(Path(self.directory.name) / 'model.usda'))
        UsdGeom.SetStageMetersPerUnit(source, 1)
        UsdGeom.SetStageUpAxis(source, 'Z')
        root = UsdGeom.Xform.Define(source, '/Building')
        source.SetDefaultPrim(root.GetPrim())
        frame = UsdGeom.Xform.Define(source, '/Building/Default')
        original = Gf.Matrix4d().SetRotate(Gf.Rotation(Gf.Vec3d(0,0,1), 25))
        original.SetTranslateOnly(Gf.Vec3d(579347,6633555,178))
        frame.AddTransformOp().Set(original)
        source.GetRootLayer().Save()
        stage = Usd.Stage.CreateInMemory()
        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdGeom.SetStageUpAxis(stage, 'Z')
        model = UsdGeom.Xform.Define(stage, '/World/Building')
        model.GetPrim().GetReferences().AddReference(source.GetRootLayer().identifier)
        return stage, model

    def test_reference_offset_is_not_applied_twice_and_parent_motion_is_applied(self):
        Usd, UsdGeom, Gf = self.usd()
        stage, model = self.reference_stage()
        coordinates = importlib.import_module('_bcf_compat_product.bcf_coordinates')
        self.fixture()
        view = self.api.read_bcf(self.path).viewpoints[0]
        view.camera['transform'][12:15] = [579400,6633600,180]
        unmoved = coordinates.import_view(view, coordinates.stage_mapping(stage))
        for a,b in zip(unmoved.camera['transform'][12:15], view.camera['transform'][12:15]):
            self.assertAlmostEqual(a,b,places=7)
        motion = Gf.Matrix4d().SetRotate(Gf.Rotation(Gf.Vec3d(0,0,1), 90))
        motion.SetTranslateOnly(Gf.Vec3d(20,30,40))
        model.AddTransformOp().Set(motion)
        moved = coordinates.import_view(view, coordinates.stage_mapping(stage))
        expected = motion.Transform(Gf.Vec3d(*view.camera['transform'][12:15]))
        for a,b in zip(moved.camera['transform'][12:15], expected):
            self.assertAlmostEqual(a,b,places=7)
        restored = coordinates.export_view(moved)
        for a,b in zip(restored.camera['transform'], view.camera['transform']):
            self.assertAlmostEqual(a,b,places=7)

    def test_units_axis_planes_and_native_round_trip(self):
        Usd, UsdGeom, Gf = self.usd()
        stage = Usd.Stage.CreateInMemory()
        UsdGeom.SetStageMetersPerUnit(stage, .01)
        UsdGeom.SetStageUpAxis(stage, 'Y')
        coordinates = importlib.import_module('_bcf_compat_product.bcf_coordinates')
        self.fixture()
        document = self.api.read_bcf(self.path)
        from dataclasses import replace
        view = replace(document.viewpoints[0], clipping_planes=((0,0,1,-3),))
        converted = coordinates.import_view(view, coordinates.stage_mapping(stage))
        self.assertEqual(converted.camera['transform'][12:15], [100,300,-200])
        self.assertEqual(converted.clipping_planes, ((0,1,0,-300),))
        self.assertEqual(converted.camera['vertical_aperture'], 5000)
        document = replace(document, viewpoints=(converted,))
        exported = Path(self.directory.name) / 'mapped.bcf'
        self.api.write_bcf(document, exported)
        reread = self.api.read_bcf(exported)
        self.assertEqual(reread.viewpoints[0].camera, converted.camera)
        self.assertIn(converted.id, reread.native_viewpoints)
        store_api = importlib.import_module('_bcf_compat_product.store')
        plan = self.api.plan_import(reread, store_api.IssueStore(stage))
        self.assertEqual(plan.document.viewpoints[0], converted)
        with ZipFile(exported) as archive:
            from xml.etree import ElementTree as ET
            xml = ET.fromstring(archive.read(next(n for n in archive.namelist() if n.endswith('.bcfv'))))
            self.assertAlmostEqual(float(xml.findtext('.//CameraViewPoint/Z')),3)

    def test_preview_detects_reference_motion_and_multiple_instances(self):
        Usd, UsdGeom, Gf = self.usd()
        stage, model = self.reference_stage()
        store_api = importlib.import_module('_bcf_compat_product.store')
        self.fixture()
        store = store_api.IssueStore(stage)
        plan = self.api.plan_import(self.api.read_bcf(self.path), store)
        model.AddTranslateOp().Set((10,0,0))
        service = types.SimpleNamespace(stage=stage, store=store, list_issues=store.list_issues)
        with self.assertRaisesRegex(ValueError, 'coordinate frame changed'):
            self.api.apply_import(plan, {}, service)
        self.assertFalse(store.list_issues())
        other = UsdGeom.Xform.Define(stage, '/World/Other')
        other.GetPrim().GetReferences().AddReference(str(Path(self.directory.name) / 'model.usda'))
        with self.assertRaisesRegex(ValueError, 'multiple instances'):
            self.api.plan_import(self.api.read_bcf(self.path), store)

    def test_default_override_and_nonuniform_scale(self):
        Usd, UsdGeom, Gf = self.usd()
        stage, model = self.reference_stage()
        coordinates = importlib.import_module('_bcf_compat_product.bcf_coordinates')
        frame = UsdGeom.Xformable(stage.GetPrimAtPath('/World/Building/Default'))
        op = frame.GetOrderedXformOps()[0]
        original = op.Get()
        shifted = Gf.Matrix4d(original)
        shifted.SetTranslateOnly(original.ExtractTranslation() + Gf.Vec3d(10,20,30))
        op.Set(shifted)
        mapping = coordinates.stage_mapping(stage)
        point = Gf.Matrix4d(*mapping[0]).Transform(Gf.Vec3d(579400,6633600,180))
        for a,b in zip(point,(579410,6633620,210)):
            self.assertAlmostEqual(a,b,places=7)
        model.AddScaleOp().Set((1,2,1))
        with self.assertRaisesRegex(ValueError, 'uniform scale'):
            coordinates.stage_mapping(stage)

    def test_ifcsite_frame_maps_camera_with_unrelated_references(self):
        Usd, UsdGeom, Gf = self.usd()
        from pxr import Sdf
        stage, model = self.reference_stage()
        source = Usd.Stage.Open(str(Path(self.directory.name) / 'model.usda'))
        site = source.GetPrimAtPath('/Building/Default')
        site.CreateAttribute('omni:hoops:metadata:TYPE', Sdf.ValueTypeNames.String).Set('IFCSITE')
        source.GetRootLayer().Save()
        accessory = Usd.Stage.CreateNew(str(Path(self.directory.name) / 'accessory.usda'))
        accessory.SetDefaultPrim(UsdGeom.Xform.Define(accessory, '/Accessory').GetPrim())
        accessory.GetRootLayer().Save()
        UsdGeom.Xform.Define(stage, '/World/Accessory').GetPrim().GetReferences().AddReference(accessory.GetRootLayer().identifier)
        coordinates = importlib.import_module('_bcf_compat_product.bcf_coordinates')
        self.fixture()
        view = self.api.read_bcf(self.path).viewpoints[0]
        view.camera['transform'][12:15] = [579400,6633600,180]
        mapping = coordinates.stage_mapping(stage)
        self.assertEqual(mapping[3], '/World/Building/Default')
        converted = coordinates.import_view(view, mapping)
        for a,b in zip(converted.camera['transform'][12:15], view.camera['transform'][12:15]):
            self.assertAlmostEqual(a,b,places=7)
        motion = Gf.Matrix4d().SetRotate(Gf.Rotation(Gf.Vec3d(0,0,1), 90))
        motion.SetTranslateOnly(Gf.Vec3d(20,30,40))
        model.AddTransformOp().Set(motion)
        converted = coordinates.import_view(view, coordinates.stage_mapping(stage))
        expected = motion.Transform(Gf.Vec3d(*view.camera['transform'][12:15]))
        for a,b in zip(converted.camera['transform'][12:15], expected):
            self.assertAlmostEqual(a,b,places=7)
        for a,b in zip(coordinates.export_view(converted).camera['transform'], view.camera['transform']):
            self.assertAlmostEqual(a,b,places=7)

    def test_multiple_ifcsite_frames_report_site_paths(self):
        Usd, UsdGeom, Gf = self.usd()
        from pxr import Sdf
        stage = Usd.Stage.CreateInMemory()
        for path in ('/World/SiteA', '/World/SiteB'):
            UsdGeom.Xform.Define(stage, path).GetPrim().CreateAttribute(
                'omni:hoops:metadata:TYPE', Sdf.ValueTypeNames.String).Set('IFCSITE')
        coordinates = importlib.import_module('_bcf_compat_product.bcf_coordinates')
        with self.assertRaisesRegex(ValueError, 'multiple IFCSITE.*SiteA.*SiteB'):
            coordinates.stage_mapping(stage)

    def test_local_ifcsite_uses_stage_world_frame(self):
        Usd, UsdGeom, Gf = self.usd()
        from pxr import Sdf
        stage = Usd.Stage.CreateInMemory()
        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdGeom.SetStageUpAxis(stage, 'Z')
        site = UsdGeom.Xform.Define(stage, '/World/Site')
        site.GetPrim().CreateAttribute('omni:hoops:metadata:TYPE', Sdf.ValueTypeNames.String).Set('IFCSITE')
        site.AddTranslateOp().Set((579347,6633555,178))
        coordinates = importlib.import_module('_bcf_compat_product.bcf_coordinates')
        mapping = coordinates.stage_mapping(stage)
        self.assertEqual(mapping[3], '/World/Site')
        self.assertEqual(Gf.Matrix4d(*mapping[0]), Gf.Matrix4d(1))

    def test_selected_ifcsite_maps_only_its_instance_and_checks_preview(self):
        Usd, UsdGeom, Gf = self.usd()
        from pxr import Sdf
        stage, model = self.reference_stage()
        source_path = str(Path(self.directory.name) / 'model.usda')
        source = Usd.Stage.Open(source_path)
        source.GetPrimAtPath('/Building/Default').CreateAttribute(
            'omni:hoops:metadata:TYPE', Sdf.ValueTypeNames.String).Set('IFCSITE')
        source.GetRootLayer().Save()
        other = UsdGeom.Xform.Define(stage, '/World/Other')
        other.GetPrim().GetReferences().AddReference(source_path)
        other.AddTranslateOp().Set((10,20,30))
        store_api = importlib.import_module('_bcf_compat_product.store')
        coordinates = importlib.import_module('_bcf_compat_product.bcf_coordinates')
        store = store_api.IssueStore(stage)
        self.fixture()
        document = self.api.read_bcf(self.path)
        with self.assertRaises(coordinates.ReferenceSelectionRequired) as raised:
            self.api.plan_import(document, store)
        self.assertEqual(set(raised.exception.paths), {'/World/Building/Default', '/World/Other/Default'})
        plan = self.api.plan_import(document, store, reference_path='/World/Other/Default')
        for actual, expected in zip(plan.document.viewpoints[0].camera['transform'][12:15], (11,22,33)):
            self.assertAlmostEqual(actual, expected, places=7)
        self.assertFalse(store.list_issues())
        service = types.SimpleNamespace(stage=stage, store=store, list_issues=store.list_issues,
                                        mutate=lambda operation: operation())
        other.GetOrderedXformOps()[0].Set((20,20,30))
        with self.assertRaisesRegex(ValueError, 'coordinate frame changed'):
            self.api.apply_import(plan, {}, service)
        self.assertFalse(store.list_issues())
        plan = self.api.plan_import(document, store, reference_path='/World/Other/Default')
        self.assertEqual(self.api.apply_import(plan, {}, service).created, 1)
        for actual, expected in zip(store.get_viewpoint(document.viewpoints[0].id).camera['transform'][12:15], (21,22,33)):
            self.assertAlmostEqual(actual, expected, places=7)

    def test_selected_reference_must_still_be_an_ifcsite(self):
        Usd, UsdGeom, Gf = self.usd()
        from pxr import Sdf
        stage = Usd.Stage.CreateInMemory()
        site = UsdGeom.Xform.Define(stage, '/World/Site').GetPrim()
        marker = site.CreateAttribute('omni:hoops:metadata:TYPE', Sdf.ValueTypeNames.String)
        marker.Set('IFCSITE')
        coordinates = importlib.import_module('_bcf_compat_product.bcf_coordinates')
        with self.assertRaisesRegex(ValueError, 'selected.*IFCSITE'):
            coordinates.stage_mapping(stage, reference_path='/World/Missing')
        marker.Set('IFCBUILDING')
        with self.assertRaisesRegex(ValueError, 'selected.*IFCSITE'):
            coordinates.stage_mapping(stage, reference_path='/World/Site')

    def test_reimport_remaps_existing_view_without_duplicating_or_replacing_evidence(self):
        Usd, UsdGeom, Gf = self.usd()
        from pxr import Sdf
        from dataclasses import replace
        stage, model = self.reference_stage()
        source_path = str(Path(self.directory.name) / 'model.usda')
        source = Usd.Stage.Open(source_path)
        source.GetPrimAtPath('/Building/Default').CreateAttribute(
            'omni:hoops:metadata:TYPE', Sdf.ValueTypeNames.String).Set('IFCSITE')
        source.GetRootLayer().Save()
        other = UsdGeom.Xform.Define(stage, '/World/Other')
        other.GetPrim().GetReferences().AddReference(source_path)
        other.AddTranslateOp().Set((10,20,30))
        store_api = importlib.import_module('_bcf_compat_product.store')
        store = store_api.IssueStore(stage)
        service = types.SimpleNamespace(stage=stage, store=store, list_issues=store.list_issues,
                                        mutate=lambda operation: operation())
        self.fixture()
        document = self.api.read_bcf(self.path)
        self.api.apply_import(self.api.plan_import(document, store, reference_path='/World/Building/Default'), {}, service)
        view_id = document.viewpoints[0].id
        issue_id = store.list_issues()[0].id
        original_issue = store.get_issue(issue_id)
        existing = store.get_viewpoint(view_id)
        # Local snapshot edits must survive a coordinate correction.
        store.put_viewpoint(replace(existing, snapshot=b'local evidence'), issue_id)
        plan = self.api.plan_import(document, store, reference_path='/World/Other/Default')
        summary = self.api.apply_import(plan, {}, service)
        for actual, expected in zip(store.get_viewpoint(view_id).camera['transform'][12:15], (11,22,33)):
            self.assertAlmostEqual(actual, expected, places=7)
        self.assertEqual(store.get_viewpoint(view_id).snapshot, b'local evidence')
        self.assertEqual(store.get_issue(issue_id), original_issue)
        self.assertEqual((summary.created, summary.comments_added, summary.viewpoints_added, summary.viewpoints_updated), (0,0,0,1))
        repeated = self.api.apply_import(self.api.plan_import(document, store, reference_path='/World/Other/Default'), {}, service)
        self.assertEqual(repeated.viewpoints_updated, 0)
        self.assertEqual(len(store.list_issues()), 1)
        stored = store.get_viewpoint(view_id)
        store.put_viewpoint(replace(stored, markup_path='/Viewport_Markups/LocalEdit'), issue_id)
        with self.assertRaisesRegex(ValueError, 'editable Markup'):
            self.api.apply_import(self.api.plan_import(document, store, reference_path='/World/Building/Default'), {}, service)
        self.assertEqual(store.get_viewpoint(view_id).camera, stored.camera)

    def test_saved_sol_scene_and_sample_share_georeferenced_frame(self):
        Usd, UsdGeom, Gf = self.usd()
        scene = Path.home() / 'OneDrive - HEMY AS/Desktop/Omniverse Working Files/PROPERTIES/SOL11-23/SOL11-23.usd'
        sample = Path.home() / 'Downloads/2026-09-30 11_36 106 Issues.bcf'
        if not scene.is_file() or not sample.is_file():
            self.skipTest('Representative local scene and archive are unavailable')
        coordinates = importlib.import_module('_bcf_compat_product.bcf_coordinates')
        stage = Usd.Stage.Open(str(scene))
        mapping = coordinates.stage_mapping(stage)
        self.assertEqual(mapping[3], '/World/SOL11_23/tn__ProjectNumber_qD/Default')
        document = self.api.read_bcf(sample)
        for view in document.viewpoints:
            if not view.camera:
                continue
            converted = coordinates.import_view(view, mapping)
            for a,b in zip(converted.camera['transform'], view.camera['transform']):
                self.assertAlmostEqual(a,b,places=6)
        self.assertFalse(stage.GetRootLayer().dirty)


if __name__ == '__main__':
    unittest.main()
