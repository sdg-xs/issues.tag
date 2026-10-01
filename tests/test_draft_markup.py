"""Offline draft-deletion ownership checks against public SDK doubles."""
import importlib.util
import asyncio
from dataclasses import dataclass
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class DraftMarkupTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        omni, kit, app, pxr = [types.ModuleType(name) for name in ('omni', 'omni.kit', 'omni.kit.app', 'pxr')]
        omni.kit, kit.app = kit, app
        pxr.Usd, pxr.UsdGeom = types.SimpleNamespace(), types.SimpleNamespace()
        modules = patch.dict(sys.modules, {'omni': omni, 'omni.kit': kit, 'omni.kit.app': app, 'pxr': pxr})
        modules.start()
        self.addCleanup(modules.stop)
        source = Path(__file__).resolve().parents[1] / 'issues_tag' / 'markup.py'
        spec = importlib.util.spec_from_file_location('_draft_markup_product', source)
        self.product = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.product)
        self.events = []
        self.stage = types.SimpleNamespace()
        self.path = '/Viewport_Markups/IssueEvidence_' + 'a' * 32
        self.native = types.SimpleNamespace(path=self.path, usd_prim=types.SimpleNamespace(GetStage=lambda: self.stage))
        self.markups = {self.path: self.native}
        self.stage.GetPrimAtPath = lambda path: self.markups.get(path)
        self.saved, self.issues = {}, []
        def get_viewpoint(view_id):
            return self.saved[view_id]
        store = types.SimpleNamespace(get_viewpoint=get_viewpoint, list_issues=lambda: self.issues,
                                      require_writable=lambda: self.events.append('writable'))
        self.context = types.SimpleNamespace(get_stage=lambda: self.stage)
        self.service = types.SimpleNamespace(stage=self.stage, generation=1, _context=self.context, store=store)
        self.adapter = self.product.MarkupAdapter(self.service)
        self.core = types.SimpleNamespace(current_markup=None, editing_markup=None)
        self.core.get_markup_from_prim_path = self.markups.get
        self.core.can_edit_markup = lambda markup, **kwargs: True
        def delete(markup):
            self.events.append('delete')
            self.markups.pop(markup.path)
        self.core.delete_markup = delete
        def end(*args, **kwargs):
            self.events.append('end edit')
            self.core.editing_markup = None
        self.core.end_edit_markup = end
        self.core.unlock_camera = lambda: self.events.append('unlock')
        self.adapter.core = self.core
        self.adapter._captured_drafts = {self.path: 1}
        self.record = types.SimpleNamespace(id='draft-id', markup_path=self.path)
        events = self.events
        class Lease:
            def __init__(self, *args):
                events.append('lease held')
            def release(self):
                events.append('lease released')
        lease = patch.object(self.product, '_RootTargetLease', Lease)
        lease.start()
        self.addCleanup(lease.stop)

    def discard(self):
        return self.adapter.discard_viewpoint(self.record, self.stage, 1)

    def test_deletes_only_owned_draft_and_is_idempotent(self):
        self.assertTrue(self.discard())
        self.assertFalse(self.discard())
        self.assertNotIn(self.path, self.markups)
        self.assertEqual(self.events, ['writable', 'lease held', 'delete', 'lease released'])

    def test_replacement_scene_and_generation_do_not_mutate(self):
        self.service.stage = object()
        self.assertFalse(self.discard())
        self.service.stage = self.stage
        self.service.generation = 2
        self.assertFalse(self.discard())
        self.assertEqual(self.events, [])

    def test_untracked_or_foreign_path_is_preserved(self):
        self.adapter._captured_drafts.clear()
        self.assertFalse(self.discard())
        self.record.markup_path = '/Viewport_Markups/ExternalEvidence'
        self.adapter._captured_drafts[self.record.markup_path] = 1
        self.assertFalse(self.discard())
        self.assertEqual(self.events, [])

    def test_saved_issue_or_comment_path_is_preserved(self):
        self.saved['saved-view'] = types.SimpleNamespace(markup_path=self.path)
        self.issues.append(types.SimpleNamespace(initial_viewpoint_id='',
            comments=(types.SimpleNamespace(viewpoint_id='saved-view'),)))
        self.assertFalse(self.discard())
        self.assertEqual(self.events, [])

    def test_saved_viewpoint_id_is_preserved(self):
        self.saved[self.record.id] = self.record
        self.assertFalse(self.discard())
        self.assertEqual(self.events, [])

    def test_vendor_edit_permission_refusal_does_not_delete(self):
        self.core.can_edit_markup = lambda *args, **kwargs: False
        with self.assertRaisesRegex(ValueError, 'delete'):
            self.discard()
        self.assertNotIn('delete', self.events)
        self.assertEqual(self.events[-1], 'lease released')

    def test_external_edit_and_review_remain_untouched(self):
        external = object()
        self.core.editing_markup = self.core.current_markup = external
        self.assertFalse(self.discard())
        self.assertEqual(self.events, [])
        self.assertIs(self.core.current_markup, external)
        self.core.editing_markup = None
        self.assertTrue(self.discard())
        self.assertIs(self.core.current_markup, external)

    def test_owned_annotation_is_released_before_delete(self):
        self.adapter._editing = self.core.editing_markup = self.core.current_markup = self.native
        self.adapter._stage, self.adapter._generation = self.stage, 1
        self.adapter._editing_active = True
        self.assertTrue(self.discard())
        self.assertLess(self.events.index('end edit'), self.events.index('delete'))
        self.assertIsNone(self.core.current_markup)

    def test_refused_delete_raises_and_retains_ownership(self):
        self.core.delete_markup = lambda markup: None
        with self.assertRaisesRegex(ValueError, 'delete'):
            self.discard()
        self.assertIn(self.path, self.adapter._captured_drafts)
        self.assertEqual(self.events[-1], 'lease released')

    def test_sdk_failure_propagates_and_releases_root_lease(self):
        def fail(markup):
            raise RuntimeError('vendor failure')
        self.core.delete_markup = fail
        with self.assertRaisesRegex(RuntimeError, 'vendor failure'):
            self.discard()
        self.assertEqual(self.events[-1], 'lease released')

    def test_destroy_removes_unsaved_draft_before_core_detaches(self):
        self.adapter.destroy()
        self.assertNotIn(self.path, self.markups, 'Destroy leaked owned unsaved native evidence')
        self.assertIsNone(self.adapter.core)

    def test_destroy_preserves_saved_and_external_owned_evidence(self):
        self.saved['saved'] = self.record
        self.issues.append(types.SimpleNamespace(initial_viewpoint_id='saved', comments=()))
        self.adapter.destroy()
        self.assertIn(self.path, self.markups)

    async def _run_failed_capture(self, cancel=False, detach=False, destroy_in_snapshot=False):
        @dataclass
        class Record:
            id: str = 'draft-id'
            markup_path: str = ''
            snapshot: bytes = b''
        sdk = types.ModuleType('omni.kit.markup.core')
        sdk.MarkupChangeCallbacks = lambda **kwargs: types.SimpleNamespace(**kwargs)
        sys.modules['omni.kit.markup.core'] = sdk
        utility = types.ModuleType('omni.kit.viewport.utility')
        delivery = asyncio.Event()
        frame_started = asyncio.Event()
        async def frame(*args):
            frame_started.set()
            await delivery.wait()
        utility.next_viewport_frame_async = frame
        sys.modules['omni.kit.viewport.utility'] = utility
        callbacks = []
        self.core.register_callback, self.core.deregister_callback = callbacks.append, callbacks.remove
        self.core.get_markup = lambda name: self.native
        async def wait():
            pass
        self.native.wait, self.native.thumbnail_data = wait, b'image'
        def create(path):
            self.markups.clear()
            self.path = self.native.path = path
            self.markups[path] = self.native
            self.core.current_markup = self.core.editing_markup = self.native
            for callback in tuple(callbacks):
                callback.on_markup_created(self.native)
        self.core.create_markup = create
        self.adapter._captured_drafts.clear()
        window = types.SimpleNamespace(viewport_api=types.SimpleNamespace(stage=self.stage))
        self.adapter._evidence_viewport = lambda: (window, types.SimpleNamespace(capture=lambda: Record()))
        async def ready():
            pass
        snapshot_started, snapshot_finished = asyncio.Event(), asyncio.Event()
        async def snapshot(*args):
            if destroy_in_snapshot:
                snapshot_started.set()
                await snapshot_finished.wait()
                return b'image'
            raise RuntimeError('PNG failure')
        self.adapter._ready, self.adapter._snapshot = ready, snapshot
        caller = asyncio.create_task(self.adapter.capture_viewpoint())
        await frame_started.wait()
        if cancel:
            caller.cancel()
            await asyncio.sleep(0)
        if detach:
            self.adapter.destroy()
            self.service._context, self.service.stage = None, None
        self.assertIn(self.path, self.markups, 'Draft was deleted before native render delivery')
        delivery.set()
        if destroy_in_snapshot:
            await snapshot_started.wait()
            self.adapter.destroy()
            self.service._context, self.service.stage = None, None
            self.assertIn(self.path, self.markups, 'Destroy deleted evidence while PNG capture was pending')
            snapshot_finished.set()
        with self.assertRaises(asyncio.CancelledError if cancel or destroy_in_snapshot else RuntimeError):
            await caller
        self.assertNotIn(self.path, self.markups, 'Unsuccessful capture leaked native evidence')

    async def test_png_failure_removes_new_native_draft(self):
        await self._run_failed_capture()

    async def test_cancelled_capture_removes_new_native_draft_after_delivery(self):
        await self._run_failed_capture(cancel=True)

    async def test_destroy_during_capture_retains_cleanup_after_service_detach(self):
        await self._run_failed_capture(cancel=True, detach=True)

    async def test_destroy_during_png_retains_cleanup_until_snapshot_completes(self):
        await self._run_failed_capture(destroy_in_snapshot=True)


if __name__ == '__main__':
    unittest.main()
