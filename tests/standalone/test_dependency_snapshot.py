import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest


class DependencySnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        path = Path(__file__).resolve().parents[2] / 'tools' / 'verification_dependencies.py'
        if not path.exists():
            self.fail('Dependency snapshot API is missing')
        spec = importlib.util.spec_from_file_location('verification_dependencies', path)
        self.api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.api)
        self.sources = {}
        for name in ('extscache', 'extscore', 'exts', 'project-exts'):
            source = self.root / 'source' / name
            source.mkdir(parents=True)
            (source / 'package.py').write_text('value = 1\n')
            self.sources[name] = source
        self.destination = self.root / 'private'

    def test_copy_breaks_shared_file_identity(self):
        source = self.sources['extscache'] / 'package.py'
        os.link(source, self.root / 'shared.py')
        self.api.prepare_snapshot(self.destination, self.sources)
        copied = self.destination / 'extscache' / 'package.py'
        self.assertEqual(copied.read_text(), source.read_text())
        self.assertEqual(copied.stat().st_nlink, 1)
        self.assertFalse(os.path.samefile(copied, source))
        self.api.validate_snapshot(self.destination)

    def test_missing_manifest_rejects_manual_shared_folders(self):
        self.destination.mkdir()
        with self.assertRaisesRegex(ValueError, 'manifest'):
            self.api.validate_snapshot(self.destination)

    def test_hard_link_added_after_copy_is_rejected(self):
        self.api.prepare_snapshot(self.destination, self.sources)
        os.link(self.destination / 'extscache' / 'package.py', self.root / 'outside.py')
        with self.assertRaisesRegex(ValueError, 'link'):
            self.api.validate_snapshot(self.destination)

    def test_missing_package_file_is_rejected(self):
        self.api.prepare_snapshot(self.destination, self.sources)
        (self.destination / 'extscache' / 'package.py').unlink()
        with self.assertRaisesRegex(ValueError, 'count|empty'):
            self.api.validate_snapshot(self.destination)

    def test_prepare_does_not_overwrite_partial_snapshot(self):
        self.destination.mkdir()
        marker = self.destination / 'keep.txt'
        marker.write_text('keep')
        with self.assertRaisesRegex(ValueError, 'existing|manifest'):
            self.api.prepare_snapshot(self.destination, self.sources)
        self.assertEqual(marker.read_text(), 'keep')

    def test_repeated_prepare_keeps_valid_snapshot(self):
        self.api.prepare_snapshot(self.destination, self.sources)
        before = (self.destination / 'snapshot.json').read_bytes()
        self.api.prepare_snapshot(self.destination, self.sources)
        self.assertEqual((self.destination / 'snapshot.json').read_bytes(), before)

    def test_loaded_shared_extension_path_is_rejected(self):
        if not hasattr(self.api, 'qualify_extension_paths'):
            self.fail('Loaded extension path qualification is missing')
        project = self.root / 'project'
        project.mkdir()
        with self.assertRaisesRegex(ValueError, 'outside'):
            self.api.qualify_extension_paths([('viewport', self.sources['extscache'])], self.destination, project)

    def test_sdk_exts_folder_may_be_empty(self):
        (self.sources['exts'] / 'package.py').unlink()
        self.api.prepare_snapshot(self.destination, self.sources)
        self.api.validate_snapshot(self.destination)

    def test_generated_bytecode_does_not_invalidate_snapshot(self):
        self.api.prepare_snapshot(self.destination, self.sources)
        cache = self.destination / 'extscache' / '__pycache__'
        cache.mkdir()
        (cache / 'package.cpython-312.pyc').write_bytes(b'generated')
        self.api.validate_snapshot(self.destination)

    def test_nested_dependencies_are_rejected_before_extension_unload(self):
        project = self.root / 'project'
        for dependency, extension in ((project / 'dependencies', project), (project, project), (project, project / 'issues.tag')):
            with self.assertRaisesRegex(ValueError, 'overlap'):
                self.api.qualify_extension_paths([], dependency, extension)

    def test_loaded_private_and_project_paths_are_accepted(self):
        if not hasattr(self.api, 'qualify_extension_paths'):
            self.fail('Loaded extension path qualification is missing')
        project = self.root / 'project'
        project.mkdir()
        paths = [('viewport', self.destination / 'extscache' / 'viewport'), ('issues.tag', project)]
        self.assertEqual(len(self.api.qualify_extension_paths(paths, self.destination, project)), 2)


if __name__ == '__main__':
    unittest.main()
