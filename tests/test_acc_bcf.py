"""Title/type exchange and repeat imports through real project records."""
from dataclasses import replace
import importlib
from pathlib import Path
import tempfile
import unittest
from uuid import uuid4
from zipfile import ZipFile
from xml.etree import ElementTree as ET

from test_acc_persistence import persistence_sdk, session_api


class AccBcfTests(unittest.TestCase):
    def setUp(self):
        manager = persistence_sdk()
        self.sdk = manager.__enter__()
        self.addCleanup(manager.__exit__, None, None, None)
        self.bcf = importlib.import_module(self.sdk.package + '.bcf')
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / 'sample.bcf'

    def issue(self, **fields):
        model = self.sdk.model
        topic = str(uuid4())
        return model.IssueRecord(topic, 'Full description', model.Status.IN_PROGRESS,
            'Reviewer', '2026-09-01T12:00:00+00:00', '2026-09-01T12:00:00+00:00', 'Reviewer',
            title='Opening clearance', issue_type='Clash', bcf_topic_id=topic, **fields)

    def document(self, issue):
        return self.bcf.BcfDocument((issue,), ())

    def test_title_type_status_description_round_trip_and_extensions(self):
        issue = self.issue()
        self.bcf.write_bcf(self.document(issue), self.path)
        reread = self.bcf.read_bcf(self.path).issues[0]
        self.assertEqual((reread.title, reread.issue_type, reread.status.value, reread.description),
            ('Opening clearance', 'Clash', 'In progress', 'Full description'))
        with ZipFile(self.path) as archive:
            extensions = ET.fromstring(archive.read('extensions.xml'))
            self.assertEqual(extensions.findtext('TopicTypes/TopicType'), 'Clash')

    def test_legacy_title_fallback_and_explicit_title_without_description(self):
        issue = self.issue()
        for title, description, expected in (('', 'First line\nMore details', 'First line'),
                ('Title only', '', 'Title only')):
            with self.subTest(title=title, description=description):
                self.bcf.write_bcf(self.document(replace(issue, title=title, description=description)), self.path)
                reread = self.bcf.read_bcf(self.path).issues[0]
                self.assertEqual(reread.title, expected)
                self.assertEqual(reread.description, description)
        with self.assertRaises(ValueError):
            self.bcf.write_bcf(self.document(replace(issue, title='', description='')), self.path)

    def test_title_type_conflicts_and_repeat_import_preserve_number_comments(self):
        service = self.sdk.service
        comment = self.sdk.model.CommentRecord(str(uuid4()), 'Partner comment', 'Partner', '2026-09-01T12:00:00+00:00')
        incoming = self.issue(comments=(comment,))
        document = self.document(incoming)
        first = self.bcf.apply_import(self.bcf.plan_import(document, service.store), {}, service)
        self.assertEqual((first.created, first.comments_added), (1, 1))
        record = service.get_issue(incoming.id)
        self.assertEqual(record.number, 1)
        service.create_type('Structure')
        edit = session_api(self.sdk, self).edit(service, incoming.id)
        edit.update(title='Local title', issue_type='Structure')
        service.commit_session(edit)
        changed = self.document(replace(incoming, title='Partner title', issue_type='Quality'))
        plan = self.bcf.plan_import(changed, service.store)
        self.assertEqual({c.field for c in plan.conflicts}, {'title', 'issue_type'})
        before = service.stage.GetRootLayer().ExportToString()
        with self.assertRaises(ValueError):
            self.bcf.apply_import(plan, {}, service)
        self.assertEqual(service.stage.GetRootLayer().ExportToString(), before)
        self.bcf.apply_import(plan, {c.key: 'keep_local' for c in plan.conflicts}, service)
        self.assertEqual((service.get_issue(incoming.id).title, service.get_issue(incoming.id).issue_type), ('Local title', 'Structure'))
        plan = self.bcf.plan_import(changed, service.store)
        self.bcf.apply_import(plan, {c.key: 'use_imported' for c in plan.conflicts}, service)
        record = service.get_issue(incoming.id)
        self.assertEqual((record.title, record.issue_type, record.number), ('Partner title', 'Quality', 1))
        self.assertEqual(record.comments, (comment,))
        repeated = self.bcf.apply_import(self.bcf.plan_import(changed, service.store), {}, service)
        self.assertEqual((repeated.created, repeated.updated, repeated.comments_added, repeated.viewpoints_added), (0, 0, 0, 0))
        self.assertEqual(len(service.list_issues()), 1)

    def test_import_assigns_project_numbers_instead_of_foreign_numbers(self):
        service = self.sdk.service
        draft = session_api(self.sdk, self).create(service, None, 'Default', None)
        draft.update(title='Local')
        local_id = service.commit_session(draft)
        first, second = self.issue(number=1), self.issue(number=1)
        document = self.bcf.BcfDocument((first, second), ())
        self.bcf.apply_import(self.bcf.plan_import(document, service.store), {}, service)
        self.assertEqual([service.get_issue(i).number for i in (local_id, first.id, second.id)], [1, 2, 3])
        repeated = self.bcf.apply_import(self.bcf.plan_import(document, service.store), {}, service)
        self.assertEqual((repeated.created, repeated.updated), (0, 0))
        self.assertEqual([service.get_issue(i).number for i in (local_id, first.id, second.id)], [1, 2, 3])
