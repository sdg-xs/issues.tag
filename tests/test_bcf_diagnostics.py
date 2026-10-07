"""Source camera evidence and offline diagnostics without a Kit application."""
import copy
from dataclasses import replace
import importlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from uuid import uuid4
from zipfile import ZipFile

import test_bcf_compat as compat
ROOT = compat.ROOT
Image = compat.Image


class CameraDiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        package = types.ModuleType('_bcf_diagnostics_product')
        package.__path__ = [str(ROOT / 'issues_tag')]
        sys.modules[package.__name__] = package
        cls.api = importlib.import_module(package.__name__ + '.bcf')
        cls.coordinates = importlib.import_module(package.__name__ + '.bcf_coordinates')

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'source.bcf'

    def fixture(self, *, version='2.1', positions=((12, -4, 1),), camera=True,
                snapshot=True, missing_snapshot=False, perspective=True):
        topic = str(uuid4())
        view_ids = [str(uuid4()) for _ in positions]
        entries = []
        image = io.BytesIO()
        Image.new('RGB', (300, 200)).save(image, format='PNG')
        with ZipFile(self.path, 'w') as archive:
            archive.writestr('bcf.version', f'<Version VersionId="{version}"/>')
            if version == '3.0':
                archive.writestr('extensions.xml', '<Extensions/>')
            for identity, position in zip(view_ids, positions):
                vectors = ''.join('<' + name + '>' + ''.join(
                    f'<{axis}>{value}</{axis}>' for axis, value in zip('XYZ', values)
                ) + '</' + name + '>' for name, values in (
                    ('CameraViewPoint', position), ('CameraDirection', (0, 0, -2)),
                    ('CameraUpVector', (0, 3, 1))))
                kind = 'PerspectiveCamera' if perspective else 'OrthogonalCamera'
                scale = '<FieldOfView>60</FieldOfView>' if perspective else '<ViewToWorldScale>5</ViewToWorldScale>'
                aspect = '<AspectRatio>1.5</AspectRatio>' if version == '3.0' else ''
                visual = f'<VisualizationInfo Guid="{identity}">' + (
                    f'<{kind}>{vectors}{scale}{aspect}</{kind}>' if camera else '') + '</VisualizationInfo>'
                archive.writestr(f'{topic}/{identity}.bcfv', visual)
                snap = f'<Snapshot>{identity}.png</Snapshot>' if snapshot else ''
                tag = 'Viewpoints' if version == '2.1' else 'ViewPoint'
                entries.append(f'<{tag} Guid="{identity}"><Viewpoint>{identity}.bcfv</Viewpoint>{snap}</{tag}>')
                if snapshot and not missing_snapshot:
                    archive.writestr(f'{topic}/{identity}.png', image.getvalue())
            views = ''.join(entries)
            topic_xml = f'<Topic Guid="{topic}" TopicType="Issue" TopicStatus="Open"><Title>Camera</Title><Description>Private description</Description><CreationDate>2026-10-07T12:00:00+00:00</CreationDate><CreationAuthor>Tester</CreationAuthor>'
            markup = ('<Markup>' + topic_xml + '</Topic>' + views + '</Markup>' if version == '2.1'
                      else '<Markup>' + topic_xml + '<Viewpoints>' + views + '</Viewpoints></Topic></Markup>')
            archive.writestr(f'{topic}/markup.bcf', markup)
        return topic, view_ids

    def diagnostics(self, *args):
        self.assertTrue((ROOT / 'issues_tag/bcf_diagnostics.py').is_file(), 'Camera diagnostics API is missing')
        api = importlib.import_module('_bcf_diagnostics_product.bcf_diagnostics')
        return api.camera_diagnostics(*args)

    def test_source_camera_survives_mapping_and_native_roundtrip(self):
        usd_fixture = compat.BcfCompatibilityTests()
        self.addCleanup(usd_fixture.doCleanups)
        Usd, UsdGeom, _ = usd_fixture.usd()
        stage = Usd.Stage.CreateInMemory()
        UsdGeom.SetStageMetersPerUnit(stage, .01)
        UsdGeom.SetStageUpAxis(stage, 'Y')
        for version, perspective in (('2.1', True), ('3.0', True), ('2.1', False)):
            with self.subTest(version=version, perspective=perspective):
                self.fixture(version=version, perspective=perspective)
                document = self.api.read_bcf(self.path)
                source = document.viewpoints[0].coordinate_frame.get('bcf_source_camera')
                self.assertEqual(source, {
                    'version': version, 'position': [12.0, -4.0, 1.0],
                    'direction': [0.0, 0.0, -2.0], 'up': [0.0, 3.0, 1.0],
                    'field_of_view': 60.0 if perspective else None,
                    'view_to_world_scale': None if perspective else 5.0,
                    'aspect_ratio': 1.5,
                })
                converted = self.coordinates.import_view(document.viewpoints[0], self.coordinates.stage_mapping(stage))
                self.assertEqual(converted.camera['transform'][12:15], [1200, 100, 400])
                exported = Path(self.directory.name) / 'native.bcf'
                self.api.write_bcf(replace(document, viewpoints=(converted,)), exported)
                reread = self.api.read_bcf(exported)
                self.assertEqual(reread.viewpoints[0].coordinate_frame['bcf_source_camera'], source)
                self.assertEqual(reread.viewpoints[0].camera, converted.camera)
                self.assertIn(converted.id, reread.native_viewpoints)

    def test_report_does_not_mutate_or_infer_origin(self):
        topic, identities = self.fixture(positions=((12, -4, 1), (579400, 6633600, 180)))
        document = self.api.read_bcf(self.path)
        before = copy.deepcopy(document)
        rows = self.diagnostics(document)
        self.assertIsInstance(rows, tuple)
        self.assertEqual([row['source_position'] for row in rows], [[12, -4, 1], [579400, 6633600, 180]])
        self.assertTrue(all(row['converted_position'] is None for row in rows))
        self.assertTrue(all(row['topic_ids'] == [topic] for row in rows))
        self.assertEqual([row['viewpoint_id'] for row in rows], identities)
        self.assertTrue(all(row['coordinate_mode'] == 'source_world' for row in rows))
        self.assertTrue(all(row['fov_mode'] == 'file' for row in rows))
        self.assertTrue(all(row['source_fov_degrees'] == 60 and row['source_aspect_ratio'] == 1.5 for row in rows))
        self.assertNotIn('Private description', json.dumps(rows))
        self.assertTrue(all('snapshot' not in row and 'description' not in row for row in rows))
        rows[0]['source_position'][0] = -999
        self.assertEqual(document, before)
        converted_view = replace(document.viewpoints[0], coordinate_frame=dict(document.viewpoints[0].coordinate_frame, bcf_reference_prim='/World/Site'))
        converted = replace(document, viewpoints=(converted_view,))
        rows = self.diagnostics(document, converted)
        self.assertEqual(rows[0]['reference_path'], '/World/Site')
        self.assertEqual(rows[0]['converted_position'], [12, -4, 1])
        self.assertIsNone(rows[1]['converted_position'])
        exported = Path(self.directory.name) / 'unlinked-view.bcf'
        self.api.write_bcf(document, exported)
        reread_rows = self.diagnostics(self.api.read_bcf(exported))
        self.assertEqual([row['viewpoint_id'] for row in reread_rows], identities)
        self.assertTrue(all(row['topic_ids'] == [topic] for row in reread_rows))

    def test_snapshot_only_and_missing_snapshot_report(self):
        self.fixture(camera=False)
        document = self.api.read_bcf(self.path)
        row = self.diagnostics(document)[0]
        self.assertIsNone(row['source_position'])
        self.assertIsNone(row['converted_position'])
        self.assertIsNone(row['source_fov_degrees'])
        self.assertNotIn('bcf_source_camera', document.viewpoints[0].coordinate_frame)
        self.assertTrue(any('without a camera' in warning for warning in document.warnings))
        self.fixture(snapshot=False)
        document = self.api.read_bcf(self.path)
        self.assertEqual(self.diagnostics(document)[0]['source_aspect_ratio'], 1.0)
        self.assertTrue(any('assumed 1:1' in warning for warning in document.warnings))
        self.fixture(missing_snapshot=True)
        with self.assertRaisesRegex(ValueError, 'missing snapshot'):
            self.api.read_bcf(self.path)

    def test_cli_json_reports_mapping_without_writing_inputs(self):
        self.fixture()
        usd_fixture = compat.BcfCompatibilityTests()
        self.addCleanup(usd_fixture.doCleanups)
        Usd, UsdGeom, _ = usd_fixture.usd()
        scene = Path(self.directory.name) / 'scene.usda'
        stage = Usd.Stage.CreateNew(str(scene))
        UsdGeom.SetStageMetersPerUnit(stage, .01)
        UsdGeom.SetStageUpAxis(stage, 'Y')
        stage.GetRootLayer().Save()
        originals = (self.path.read_bytes(), scene.read_bytes())
        tool = ROOT / 'tools/bcf_camera_report.py'
        self.assertTrue(tool.is_file(), 'Offline camera report CLI is missing')
        result = subprocess.run([sys.executable, str(tool), str(self.path), '--scene', str(scene)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['cameras'][0]['converted_position'], [1200, 100, 400])
        self.assertEqual(payload['mapping']['up_axis'], 'Y')
        self.assertEqual(payload['mapping']['meters_per_unit'], .01)
        self.assertEqual((self.path.read_bytes(), scene.read_bytes()), originals)


if __name__ == '__main__':
    unittest.main()
