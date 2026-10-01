"""Creation retries keep the same draft and accept only a complete Save."""
import unittest
from test_acc_controller import controller_sdk


class IssueCreationTests(unittest.IsolatedAsyncioTestCase):
    async def test_invalid_title_then_save_preserves_draft_identity(self):
        with controller_sdk(self) as sdk:
            await sdk.extension._create_issue_from_pin(None)
            draft = sdk.extension._session
            self.assertIsNone(await sdk.extension.save_details())
            self.assertIs(sdk.extension._session, draft)
            draft.update(title='Clearance', description='Check clearance')
            issue_id = await sdk.extension.save_details()
            self.assertEqual(issue_id, draft.record.id)
            self.assertEqual(sdk.service.get_issue(issue_id).description, 'Check clearance')
            self.assertEqual(len(sdk.service.list_issues()), 1)

    async def test_capture_failure_keeps_details_available_for_retry_or_discard(self):
        with controller_sdk(self) as sdk:
            async def fail(): raise ValueError('Capture failed')
            sdk.markup.capture_viewpoint = fail
            await sdk.extension._create_issue_from_pin(None)
            self.assertIsNotNone(sdk.extension._session)
            self.assertIn('Capture failed', sdk.extension._details.error)
            self.assertEqual(sdk.service.list_issues(), ())
            await sdk.extension.cancel_details('discard')
            self.assertIsNone(sdk.extension._details)
