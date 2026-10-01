"""Offline staged Save and migration checks using real USD and issue commands."""
from contextlib import contextmanager
from dataclasses import replace
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
LIBRARIES = Path.home() / '.codex/worktrees/issues-tag-improvements/verification-dependencies/extscache'
USD = next(LIBRARIES.glob('omni.usd.libs-*'))
DLL_HANDLE = os.add_dll_directory(str(USD / 'bin'))
sys.path.insert(0, str(USD))
sys.path.insert(0, str(ROOT / 'verification/python'))
from pxr import Sdf, Tf, Usd


@contextmanager
def persistence_sdk():
    modules = {}
    def module(name, **values):
        item = types.ModuleType(name)
        item.__path__ = []
        item.__dict__.update(values)
        modules[name] = item
        if '.' in name and name.rsplit('.', 1)[0] in modules:
            setattr(modules[name.rsplit('.', 1)[0]], name.rsplit('.', 1)[1], item)
        return item
    settings = {}
    module('carb')
    module('carb.settings', get_settings=lambda: types.SimpleNamespace(get=settings.get, set=settings.__setitem__))
    module('omni')
    module('omni.kit')
    commands = module('omni.kit.commands', Command=object, register=lambda cls: None)
    context = types.SimpleNamespace(get_stage=lambda: context.stage,
        stage=Usd.Stage.CreateInMemory(), get_stage_event_stream=lambda: types.SimpleNamespace(
            create_subscription_to_pop=lambda callback: None))
    module('omni.usd', get_context=lambda: context,
        StageEventType=types.SimpleNamespace(OPENED=1, CLOSED=2))
    package = module('_acc_persistence_product', __path__=[str(ROOT / 'issues_tag')])
    with patch.dict(sys.modules, modules):
        api = importlib.import_module(package.__name__ + '.service')
        command_api = importlib.import_module(package.__name__ + '.commands')
        commands.execute = lambda name, **kwargs: (True, command_api.UpdateIssuesCommand(**kwargs).do())
        model = importlib.import_module(package.__name__ + '.model')
        store = importlib.import_module(package.__name__ + '.store')
        service = api.IssueService()
        try:
            yield types.SimpleNamespace(service=service, context=context, model=model, store=store, package=package.__name__)
        finally:
            service.destroy()
            for name in list(sys.modules):
                if name.startswith(package.__name__ + '.'):
                    sys.modules.pop(name, None)


def session_api(sdk, testcase):
    testcase.assertTrue((ROOT / 'issues_tag/edit_session.py').is_file(), 'Staged edit sessions are missing')
    return importlib.import_module(sdk.package + '.edit_session').IssueEditSession


class AccPersistenceTests(unittest.TestCase):
    def setUp(self):
        manager = persistence_sdk()
        self.sdk = manager.__enter__()
        self.addCleanup(manager.__exit__, None, None, None)
        self.service = self.sdk.service

    def draft(self, title='Opening'):
        session = session_api(self.sdk, self).create(self.service, None, 'Default', None)
        session.update(title=title, description='Check clearance')
        return session

    def test_title_trimmed_boundaries_and_unknown_type_have_no_partial_save(self):
        for title in ('', '   ', 'x' * 256, '  ' + 'x' * 256 + '  '):
            with self.subTest(title_length=len(title)):
                before = self.service.stage.GetRootLayer().ExportToString()
                with self.assertRaises(ValueError):
                    self.service.commit_session(self.draft(title))
                self.assertEqual(self.service.stage.GetRootLayer().ExportToString(), before)
        for title in (' x ', '  ' + 'x' * 255 + '  '):
            issue_id = self.service.commit_session(self.draft(title))
            self.assertEqual(self.service.get_issue(issue_id).title, title.strip())
        draft = self.draft()
        draft.update(issue_type='Unknown')
        before = self.service.stage.GetRootLayer().ExportToString()
        with self.assertRaises(ValueError):
            self.service.commit_session(draft)
        self.assertEqual(self.service.stage.GetRootLayer().ExportToString(), before)

    def test_save_reopen_preserves_number_fields_comments_and_parent_ownership(self):
        source = Sdf.Layer.CreateAnonymous()
        self.service.stage.GetRootLayer().subLayerPaths.append(source.identifier)
        source_before = source.ExportToString()
        self.service.stage.SetEditTarget(self.service.stage.GetSessionLayer())
        draft = self.draft(' Door ')
        draft.comment_text = ' Review clearance '
        self.service.create_type('Clash')
        draft.update(issue_type='Clash', status=self.sdk.model.Status.IN_PROGRESS)
        issue_id = self.service.commit_session(draft)
        record = self.service.get_issue(issue_id)
        self.assertEqual((record.title, record.issue_type, record.number), ('Door', 'Clash', 1))
        self.assertEqual(record.comments[0].text, 'Review clearance')
        self.assertEqual(self.service.stage.GetPrimAtPath('/Issues').GetAttribute('issues:schemaVersion').Get(), 2)
        self.assertFalse(self.service.stage.GetSessionLayer().GetPrimAtPath('/Issues'))
        self.assertEqual(source.ExportToString(), source_before)
        edit = session_api(self.sdk, self).edit(self.service, issue_id)
        edit.update(title='Saved change')
        self.service.commit_session(edit)
        self.assertEqual(self.service.get_issue(issue_id).number, 1)
        self.assertEqual(self.service.get_issue(self.service.commit_session(self.draft())).number, 2)
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / 'parent.usda')
            self.service.stage.GetRootLayer().Export(path)
            reopened = self.sdk.store.IssueStore(Usd.Stage.Open(path))
            self.assertEqual(reopened.get_issue(issue_id), self.service.get_issue(issue_id))
            self.assertEqual(reopened.list_types(), ('Default', 'Clash'))

    def test_stale_record_scene_and_read_only_reject_save(self):
        issue_id = self.service.commit_session(self.draft())
        edit = session_api(self.sdk, self).edit(self.service, issue_id)
        self.service.set_description(issue_id, 'Someone else changed it')
        before = self.service.stage.GetRootLayer().ExportToString()
        with self.assertRaises(ValueError):
            self.service.commit_session(edit)
        self.assertEqual(self.service.stage.GetRootLayer().ExportToString(), before)
        draft = self.draft()
        self.service.generation += 1
        with self.assertRaises(ValueError):
            self.service.commit_session(draft)
        draft = self.draft()
        self.sdk.context.stage = Usd.Stage.CreateInMemory()
        with self.assertRaises(ValueError):
            self.service.commit_session(draft)
        draft = self.draft()
        self.service.stage.GetRootLayer().SetPermissionToEdit(False)
        try:
            with self.assertRaises(ValueError):
                self.service.commit_session(draft)
        finally:
            self.service.stage.GetRootLayer().SetPermissionToEdit(True)
        self.assertEqual(self.service.list_issues(), ())

    def test_viewpoint_failure_rolls_back_record_number_and_pending_comment(self):
        draft = self.draft()
        draft.viewpoint = self.sdk.model.ViewpointRecord(str(uuid4()), snapshot=b'PNG')
        draft.comment_text = 'Pending'
        before = self.service.stage.GetRootLayer().ExportToString()
        def fail_after_write(store, viewpoint, issue_id=''):
            original(store, viewpoint, issue_id)
            raise ValueError('Evidence write failed')
        original = self.sdk.store.IssueStore.put_viewpoint
        with patch.object(self.sdk.store.IssueStore, 'put_viewpoint', fail_after_write):
            with self.assertRaises(ValueError):
                self.service.commit_session(draft)
        self.assertEqual(self.service.stage.GetRootLayer().ExportToString(), before)
        issue_id = self.service.commit_session(draft)
        self.assertEqual(self.service.get_issue(issue_id).number, 1)
        self.assertEqual(len(self.service.get_issue(issue_id).comments), 1)
        self.assertEqual(self.service.store.get_viewpoint(draft.viewpoint.id), draft.viewpoint)

    def test_legacy_create_action_obeys_the_same_title_and_type_validation(self):
        for fields in (dict(title='x' * 256), dict(title='   '), dict(issue_type='Unknown')):
            with self.subTest(fields=fields):
                before = self.service.stage.GetRootLayer().ExportToString()
                with self.assertRaises(ValueError):
                    self.service.create_issue('Description', **fields)
                self.assertEqual(self.service.stage.GetRootLayer().ExportToString(), before)
        issue_id = self.service.create_issue(' Description\nMore details ')
        record = self.service.get_issue(issue_id)
        self.assertEqual((record.title, record.description, record.number), ('Description', 'Description\nMore details', 1))

    def test_failed_save_of_legacy_scene_does_not_persist_migration(self):
        issue_id = self.service.create_issue('Legacy')
        prim = self.service.stage.GetPrimAtPath('/Issues/Issue_' + issue_id.replace('-', ''))
        values = json.loads(prim.GetAttribute('issues:record').Get())
        for field in ('title', 'issue_type', 'number'):
            del values[field]
        prim.GetAttribute('issues:record').Set(json.dumps(values))
        self.service.stage.GetPrimAtPath('/Issues').GetAttribute('issues:schemaVersion').Set(1)
        draft = self.draft()
        draft.viewpoint = self.sdk.model.ViewpointRecord(str(uuid4()))
        before = self.service.stage.GetRootLayer().ExportToString()
        with patch.object(self.sdk.store.IssueStore, 'put_viewpoint', side_effect=ValueError('Evidence write failed')):
            with self.assertRaises(ValueError):
                self.service.commit_session(draft)
        self.assertEqual(self.service.stage.GetRootLayer().ExportToString(), before)
        self.assertEqual(self.service.get_issue(issue_id).number, 1)
        self.assertEqual(self.service.get_issue(self.service.commit_session(draft)).number, 2)

    def test_later_edit_does_not_rewrite_an_untouched_migrated_record(self):
        stage = self.service.stage
        issue_ids = [self.service.create_issue(title) for title in ('Door', 'Ceiling')]
        paths = ['/Issues/Issue_' + issue_id.replace('-', '') for issue_id in issue_ids]
        for path in paths:
            attr = stage.GetPrimAtPath(path).GetAttribute('issues:record')
            values = json.loads(attr.Get())
            for field in ('title', 'issue_type', 'number'):
                del values[field]
            attr.Set(json.dumps(values))
        stage.GetPrimAtPath('/Issues').GetAttribute('issues:schemaVersion').Set(1)
        self.service.set_description(issue_ids[0], 'First edit')
        untouched = stage.GetPrimAtPath(paths[1])
        values = json.loads(untouched.GetAttribute('issues:record').Get())
        self.assertEqual((values['title'], values['issue_type'], values['number']), ('Ceiling', 'Default', 2))
        self.assertEqual(stage.GetPrimAtPath('/Issues').GetAttribute('issues:schemaVersion').Get(), 2)
        changed_paths = []
        def changed(notice, sender):
            changed_paths.extend(str(path) for path in notice.GetChangedInfoOnlyPaths())
            changed_paths.extend(str(path) for path in notice.GetResyncedPaths())
        subscription = Tf.Notice.Register(Usd.Notice.ObjectsChanged, changed, stage)
        writes = []
        original_set = Usd.Attribute.Set
        def record_write(attribute, *args, **kwargs):
            writes.append(str(attribute.GetPath()))
            return original_set(attribute, *args, **kwargs)
        try:
            with patch.object(Usd.Attribute, 'Set', record_write):
                self.service.set_description(issue_ids[0], 'Second edit')
        finally:
            subscription.Revoke()
        self.assertTrue(any(path.startswith(paths[0] + '.') for path in changed_paths), changed_paths)
        self.assertFalse(any(path == paths[1] or path.startswith(paths[1] + '.') for path in changed_paths), changed_paths)
        self.assertEqual([path for path in writes if path.endswith('.issues:record')], [paths[0] + '.issues:record'])
        self.assertEqual(json.loads(untouched.GetAttribute('issues:record').Get()), values)

    def test_legacy_read_is_nonmutating_and_save_migrates_stable_numbers(self):
        stage = self.service.stage
        container = stage.DefinePrim('/Issues', 'Scope')
        container.CreateAttribute('issues:schemaVersion', Sdf.ValueTypeNames.Int, custom=True).Set(1)
        ids = [str(uuid4()), str(uuid4())]
        for number, issue_id in enumerate(ids):
            values = dict(id=issue_id, description=('Door\nMore details' if number == 0 else 'Ceiling'),
                status='Open', author='Original', created_at=f'2026-09-0{number+1}T12:00:00+00:00',
                modified_at='2026-09-01T12:00:00+00:00', modified_by='Original')
            prim = stage.DefinePrim('/Issues/Issue_' + issue_id.replace('-', ''), 'Scope')
            prim.CreateAttribute('issues:record', Sdf.ValueTypeNames.String, custom=True).Set(json.dumps(values))
        before = stage.GetRootLayer().ExportToString()
        stage.GetRootLayer().SetPermissionToEdit(False)
        try:
            records = self.service.list_issues()
            self.assertTrue(hasattr(records[0], 'number'), 'Legacy display numbering is missing')
            self.assertEqual([(r.title, r.issue_type, r.number) for r in records], [('Door', 'Default', 1), ('Ceiling', 'Default', 2)])
            self.assertEqual(stage.GetRootLayer().ExportToString(), before)
        finally:
            stage.GetRootLayer().SetPermissionToEdit(True)
        edit = session_api(self.sdk, self).edit(self.service, ids[0])
        edit.update(title='Updated')
        self.service.commit_session(edit)
        self.assertEqual([r.number for r in self.service.list_issues()], [1, 2])
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / 'legacy.usda')
            stage.GetRootLayer().Export(path)
            records = self.sdk.store.IssueStore(Usd.Stage.Open(path)).list_issues()
            self.assertEqual([(r.title, r.number) for r in records], [('Updated', 1), ('Ceiling', 2)])


    def test_all_comment_and_attachment_changes_rollback_when_later_evidence_write_fails(self):
        draft = self.draft()
        issue_id = self.service.commit_session(draft)
        session = session_api(self.sdk, self).edit(self.service, issue_id)
        first = self.sdk.model.ViewpointRecord(str(uuid4()), snapshot=b'first')
        session.comment_text, session.comment_viewpoint = 'First comment', first
        session.stage_comment(self.service)
        second = self.sdk.model.ViewpointRecord(str(uuid4()), snapshot=b'second')
        session.comment_text, session.comment_viewpoint = 'Second comment', second
        ref = self.sdk.model.ElementRef('', '/Model', '/Model', prim_path='/Model')
        session.update(title='Changed', anchor=self.sdk.model.Anchor(ref, (1, 2, 3)), related_elements=(ref,))
        before = self.service.stage.GetRootLayer().ExportToString()
        put = self.sdk.store.IssueStore.put_viewpoint
        def fail_second(store, viewpoint, issue_id=''):
            if viewpoint.id == second.id:
                raise ValueError('Second evidence write failed')
            return put(store, viewpoint, issue_id)
        with patch.object(self.sdk.store.IssueStore, 'put_viewpoint', fail_second):
            with self.assertRaises(ValueError):
                self.service.commit_session(session)
        self.assertEqual(self.service.stage.GetRootLayer().ExportToString(), before)
        self.assertEqual(session.comment_viewpoint, second)
        self.service.commit_session(session)
        saved = self.service.get_issue(issue_id)
        self.assertEqual([comment.viewpoint_id for comment in saved.comments], [first.id, second.id])
        self.assertEqual(saved.anchor.local_position, (1, 2, 3))
        self.assertEqual(saved.related_elements, (ref,))

    def test_stale_saved_comment_evidence_and_readonly_reject_combined_save(self):
        draft = self.draft()
        draft.comment_text = 'Saved'
        draft.comment_viewpoint = self.sdk.model.ViewpointRecord(str(uuid4()), snapshot=b'saved')
        issue_id = self.service.commit_session(draft)
        session = session_api(self.sdk, self).edit(self.service, issue_id)
        comment_id = session.record.comments[0].id
        original = session.comment_viewpoints[comment_id]
        session.set_comment_viewpoint(comment_id, replace(original, id=str(uuid4()), snapshot=b'edited'))
        self.service.store.put_viewpoint(replace(original, snapshot=b'elsewhere'), issue_id)
        before = self.service.stage.GetRootLayer().ExportToString()
        with self.assertRaisesRegex(ValueError, 'comment evidence changed'):
            self.service.commit_session(session)
        self.assertEqual(self.service.stage.GetRootLayer().ExportToString(), before)
        fresh = session_api(self.sdk, self).edit(self.service, issue_id)
        fresh.comment_text = 'Pending'
        fresh.comment_viewpoint = self.sdk.model.ViewpointRecord(str(uuid4()), snapshot=b'pending')
        self.service.stage.GetRootLayer().SetPermissionToEdit(False)
        try:
            with self.assertRaises(ValueError): self.service.commit_session(fresh)
            self.assertEqual(self.service.stage.GetRootLayer().ExportToString(), before)
        finally:
            self.service.stage.GetRootLayer().SetPermissionToEdit(True)
