"""Draft changes preserve saved records and evidence until details Save."""
import unittest
from dataclasses import replace
from uuid import uuid4
from test_acc_persistence import persistence_sdk, session_api


class EditSessionTests(unittest.TestCase):
    def test_create_and_update_do_not_mutate_store(self):
        with persistence_sdk() as sdk:
            api = session_api(sdk, self)
            before = sdk.service.stage.GetRootLayer().ExportToString()
            session = api.create(sdk.service, None, 'Default', None)
            session.update(title='Opening', description='Check clearance')
            session.comment_text = 'Pending comment'
            self.assertTrue(session.is_new)
            self.assertTrue(session.dirty)
            self.assertEqual(session.record.number, 0)
            self.assertEqual(sdk.service.list_issues(), ())
            self.assertEqual(sdk.service.stage.GetRootLayer().ExportToString(), before)

    def test_edit_preserves_original_record_and_viewpoint(self):
        with persistence_sdk() as sdk:
            api = session_api(sdk, self)
            view = sdk.model.ViewpointRecord(str(uuid4()), camera={'projection': 'perspective'}, snapshot=b'original')
            created = api.create(sdk.service, None, 'Default', view)
            created.update(title='Original', description='Description')
            issue_id = sdk.service.commit_session(created)
            original = sdk.service.get_issue(issue_id)
            session = api.edit(sdk.service, issue_id)
            self.assertFalse(session.is_new)
            self.assertFalse(session.dirty)
            session.update(title='Edited')
            session.viewpoint.camera['projection'] = 'orthographic'
            session.viewpoint = replace(session.viewpoint, snapshot=b'changed')
            self.assertTrue(session.dirty)
            self.assertEqual(session.original, original)
            self.assertEqual(session.original_viewpoint.camera, {'projection': 'perspective'})
            self.assertEqual(session.original_viewpoint.snapshot, b'original')
            self.assertEqual(sdk.service.get_issue(issue_id), original)
            self.assertEqual(sdk.service.store.get_viewpoint(view.id), view)

    def test_stale_saved_viewpoint_rejects_commit_even_when_metadata_is_unchanged(self):
        with persistence_sdk() as sdk:
            api = session_api(sdk, self)
            view = sdk.model.ViewpointRecord(str(uuid4()), snapshot=b'original')
            created = api.create(sdk.service, None, 'Default', view)
            created.update(title='Original')
            issue_id = sdk.service.commit_session(created)
            edit = api.edit(sdk.service, issue_id)
            edit.update(title='Edited')
            sdk.service.store.put_viewpoint(replace(view, snapshot=b'changed elsewhere'), issue_id)
            before = sdk.service.stage.GetRootLayer().ExportToString()
            with self.assertRaises(ValueError):
                sdk.service.commit_session(edit)
            self.assertEqual(sdk.service.stage.GetRootLayer().ExportToString(), before)

    def test_deleted_record_is_reported_as_a_stale_draft_without_recreating_it(self):
        with persistence_sdk() as sdk:
            api = session_api(sdk, self)
            created = api.create(sdk.service, None, 'Default', None)
            created.update(title='Original')
            issue_id = sdk.service.commit_session(created)
            edit = api.edit(sdk.service, issue_id)
            sdk.service.stage.RemovePrim('/Issues/Issue_' + issue_id.replace('-', ''))
            before = sdk.service.stage.GetRootLayer().ExportToString()
            with self.assertRaises(ValueError):
                sdk.service.commit_session(edit)
            self.assertEqual(sdk.service.stage.GetRootLayer().ExportToString(), before)


    def test_comment_staging_keeps_text_evidence_and_identity_out_of_store(self):
        with persistence_sdk() as sdk:
            api = session_api(sdk, self)
            session = api.create(sdk.service, None, 'Default', None)
            session.update(title='Original')
            session.comment_text = ' First '
            session.comment_viewpoint = sdk.model.ViewpointRecord(str(uuid4()), snapshot=b'evidence')
            evidence = session.comment_viewpoint
            comment_id = session.stage_comment(sdk.service)
            self.assertEqual(session.record.comments[0].text, 'First')
            self.assertEqual(session.comment_viewpoints[comment_id], evidence)
            self.assertEqual(session.comment_text, '')
            self.assertIsNone(session.comment_viewpoint)
            self.assertEqual(sdk.service.list_issues(), ())
            issue_id = sdk.service.commit_session(session)
            edit = api.edit(sdk.service, issue_id)
            self.assertFalse(edit.dirty)
            edit.comment_viewpoints[comment_id].camera['projection'] = 'changed'
            self.assertEqual(edit.original_comment_viewpoints[comment_id].camera, {})
            self.assertEqual(sdk.service.store.get_viewpoint(evidence.id).camera, {})
            self.assertTrue(edit.dirty)
