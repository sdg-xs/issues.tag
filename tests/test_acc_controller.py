"""Controller transitions with real USD transactions and controlled native boundaries."""
import asyncio
import importlib
import sys
import types
import unittest
from contextlib import contextmanager
from dataclasses import replace
from unittest.mock import patch
from uuid import uuid4
from test_acc_persistence import persistence_sdk, session_api


class Details:
    def __init__(self, session, types, **callbacks):
        self.session, self.callbacks = session, callbacks
        self.error, self.busy, self.destroyed = '', False, False
    def sync(self): pass
    def set_error(self, message): self.error = message
    def set_busy(self, value): self.busy = value
    def refresh(self): pass
    def clear_comment(self): pass
    def destroy(self): self.destroyed = True


@contextmanager
def controller_sdk(test):
    with persistence_sdk() as sdk:
        modules = {}
        def module(name, **values):
            item = types.ModuleType(name)
            item.__dict__.update(values)
            modules[name] = item
            return item
        ext = module('omni.ext', IExt=object)
        module('omni.ui')
        module('omni.kit.menu')
        module('omni.kit.menu.utils', MenuItemDescription=lambda **kw: kw,
               add_menu_items=lambda *a: None, remove_menu_items=lambda *a: None)
        module(sdk.package + '.window', IssueDetailsWindow=Details)
        with patch.dict(sys.modules, modules), patch.object(sys.modules['omni'], 'ext', ext, create=True):
            extension = importlib.import_module(sdk.package + '.extension').IssuesController()
            service = sdk.service
            calls, discarded = [], []
            view = sdk.model.ViewpointRecord(str(uuid4()), snapshot=b'original', markup_path='/Viewport_Markups/IssueEvidence_first')
            async def placement(): return None
            viewport = types.SimpleNamespace(request_placement=placement, cancel_placement=lambda: calls.append('cancel placement'),
                restore=lambda v: calls.append('restore'), capture=lambda: view, _placement_viewport='primary',
                destroy=lambda: calls.append('viewport destroyed'))
            service.viewport = viewport
            async def capture():
                calls.append('capture')
                return replace(view, id=str(uuid4()), markup_path='/Viewport_Markups/IssueEvidence_' + uuid4().hex)
            async def begin(v): calls.append(('begin', v.id))
            async def finish(v, save=True):
                calls.append(('finish', save))
                return replace(v, snapshot=b'accepted') if save else v
            async def copy(v):
                calls.append(('copy', v.id))
                return replace(v, id=str(uuid4()), markup_path='/Viewport_Markups/IssueEvidence_' + uuid4().hex)
            markup = types.SimpleNamespace(capture_viewpoint=capture, begin=begin, finish=finish, copy_for_edit=copy,
                _evidence_viewport=lambda: (types.SimpleNamespace(viewport_api='primary'), viewport),
                discard_viewpoint=lambda v, *a: discarded.append(v) or True, destroy=lambda: calls.append('markup destroyed'))
            panel = types.SimpleNamespace(selected_issue_id=None, visible_issue_ids=frozenset(),
                clear_filters=lambda: calls.append('clear filters'), refresh=lambda: None, destroy=lambda: None,
                set_placement_state=lambda active, *a: calls.append(('placement', active)))
            extension._service, extension._viewport, extension._markup, extension._window = service, viewport, markup, panel
            extension._tasks, extension._dialogs, extension._menus = set(), [], []
            extension._session, extension._details, extension._annotation, extension._edit_task = None, None, None, None
            extension._owned_views, extension._shutting_down, extension._toolbar = {}, False, None
            yield types.SimpleNamespace(extension=extension, service=service, api=session_api(sdk, test),
                model=sdk.model, view=view, calls=calls, discarded=discarded, markup=markup, viewport=viewport)


class ControllerTests(unittest.IsolatedAsyncioTestCase):
    async def create(self, sdk):
        async def placement(): return None
        # The picked anchor is optional in the persistence model; bypass only raycast.
        await sdk.extension._create_issue_from_pin(None)
        return sdk.extension._session

    async def test_review_reselection_restores_context_without_replacing_or_saving_draft(self):
        for native in (False, True):
            with self.subTest(native=native), controller_sdk(self) as sdk:
                original = sdk.api.create(sdk.service, None, 'Default', sdk.view)
                original.update(title='Original')
                issue_id = sdk.service.commit_session(original)
                await sdk.extension.select_issue(issue_id)
                draft = sdk.extension._session
                draft.update(title='Unsaved metadata')
                draft.comment_text = 'Keep this comment'
                before = sdk.service.stage.GetRootLayer().ExportToString()
                recalled = []
                sdk.service.native_view_recaller = lambda view: recalled.append(('native', view)) or native
                sdk.viewport.restore = lambda view: recalled.append(('portable', view))
                self.assertEqual(await sdk.extension.select_issue(issue_id), issue_id)
                self.assertEqual(recalled, [('native', sdk.view)] + ([] if native else [('portable', sdk.view)]))
                self.assertIs(sdk.extension._session, draft)
                self.assertEqual(draft.record.title, 'Unsaved metadata')
                self.assertEqual(draft.comment_text, 'Keep this comment')
                self.assertEqual(sdk.service.stage.GetRootLayer().ExportToString(), before)
                self.assertFalse(sdk.discarded)

    async def test_review_action_finishes_owned_initial_and_comment_evidence_before_recall(self):
        for target in ('initial', 'pending', 'saved comment'):
            with self.subTest(target=target), controller_sdk(self) as sdk:
                draft = await self.create(sdk)
                draft.update(title='Draft')
                if target != 'initial':
                    await sdk.extension.capture_comment_viewpoint()
                    draft.comment_text = 'Retained comment'
                    if target == 'saved comment':
                        comment_id = await sdk.extension.add_comment()
                        await sdk.extension.annotate_comment(comment_id)
                    else:
                        await sdk.extension.annotate_comment()
                annotation = sdk.extension._annotation
                recalled = []
                sdk.service.native_view_recaller = lambda view: recalled.append(view) or True
                callback = sdk.extension._details.callbacks['on_open_review_view']
                await callback()
                accepted = (draft.viewpoint if target == 'initial' else draft.comment_viewpoint
                            if target == 'pending' else draft.comment_viewpoints[comment_id])
                self.assertEqual(accepted.id, annotation.id)
                self.assertEqual(accepted.snapshot, b'accepted')
                self.assertEqual(recalled, [draft.viewpoint])
                self.assertIs(sdk.extension._session, draft)
                self.assertIn(accepted.id, sdk.extension._owned_views)
                self.assertIsNone(sdk.extension._annotation)
                self.assertFalse(sdk.discarded)
                self.assertEqual(sdk.service.list_issues(), ())

    async def test_review_capture_failure_stops_navigation_and_retains_retryable_draft(self):
        with controller_sdk(self) as sdk:
            draft = await self.create(sdk)
            annotation = sdk.extension._annotation
            async def fail(*args, **kwargs):
                raise ValueError('Snapshot failed before recall')
            sdk.markup.finish = fail
            recalled = []
            sdk.service.native_view_recaller = lambda view: recalled.append(view) or True
            await sdk.extension._details.callbacks['on_open_review_view']()
            self.assertEqual(recalled, [])
            self.assertIs(sdk.extension._session, draft)
            self.assertIs(sdk.extension._annotation, annotation)
            self.assertIn('Snapshot failed', sdk.extension._details.error)
            self.assertFalse(sdk.extension._details.busy)
            self.assertFalse(sdk.discarded)

    async def test_real_session_dirty_guidance_tracks_edits_reverts_and_evidence(self):
        from test_acc_ui import Combo, Widget, panel_types
        with controller_sdk(self) as sdk:
            original = sdk.api.create(sdk.service, None, 'Default', None)
            original.update(title='Original')
            issue_id = sdk.service.commit_session(original)
            draft = sdk.api.edit(sdk.service, issue_id)
            _, DetailsPanel = panel_types()
            panel = DetailsPanel(draft, ('Default', 'Quality'), on_save=None, on_cancel=None,
                                 on_annotate=None, on_replace=None, on_comment_view=None)
            try:
                clean = 'No unsaved issue edits. Scene Save writes committed changes to disk.'
                dirty = 'Unsaved issue edits. Save issue, then save scene.'
                before = sdk.service.stage.GetRootLayer().ExportToString()
                for field in ('title', 'description', 'comment'):
                    model = getattr(panel, field)
                    value = model.as_string
                    count = panel.window.build_count
                    self.assertEqual(panel._draft_state.text, clean)
                    model.set_value('Changed')
                    self.assertEqual(panel._draft_state.text, dirty)
                    model.set_value(value)
                    self.assertEqual(panel._draft_state.text, clean)
                    self.assertEqual(panel.window.build_count, count)
                for choice in [w for w in Widget.widgets if isinstance(w, Combo)][-2:]:
                    choice.model.choose(1)
                    self.assertEqual(panel._draft_state.text, dirty)
                    choice.model.choose(0)
                    self.assertEqual(panel._draft_state.text, clean)
                draft.comment_viewpoint = replace(sdk.view, snapshot=b'')
                panel.set_busy(False)
                self.assertEqual(panel._draft_state.text, dirty)
                draft.comment_viewpoint = None
                panel.refresh()
                self.assertEqual(panel._draft_state.text, clean)
                draft.viewpoint = replace(sdk.view, snapshot=b'')
                panel.refresh()
                self.assertEqual(panel._draft_state.text, dirty)
                self.assertEqual(sdk.service.stage.GetRootLayer().ExportToString(), before)
            finally:
                panel.destroy()
            for model in (panel.title, panel.description, panel.comment):
                self.assertFalse(model.callbacks)

    async def test_module_reload_preservation_uses_full_serialized_records(self):
        with controller_sdk(self) as sdk:
            draft = sdk.api.create(sdk.service, None, 'Default', sdk.view)
            draft.update(title='Reload boundary', description='All fields survive')
            draft.comment_text = 'Saved comment'
            issue_id = sdk.service.commit_session(draft)
            issue = sdk.service.get_issue(issue_id)
            saved = sdk.service.store.get_viewpoint(sdk.view.id)
            old_store = importlib.import_module(sdk.api.__module__.rsplit('.', 1)[0] + '.store')
            expected_issue, expected_view = old_store.encode(issue), old_store.encode(saved)
            before = sdk.service.stage.GetRootLayer().ExportToString()
            for suffix in ('.store', '.model'):
                sys.modules.pop(sdk.api.__module__.rsplit('.', 1)[0] + suffix)
            store_module = importlib.import_module(old_store.__name__)
            store = store_module.IssueStore(sdk.service.stage)
            loaded_issue, loaded_view = store.get_issue(issue_id), store.get_viewpoint(saved.id)
            self.assertNotEqual(loaded_issue, issue)
            self.assertNotEqual(loaded_view, saved)
            self.assertEqual(store_module.encode(loaded_issue), expected_issue)
            self.assertEqual(store_module.encode(loaded_view), expected_view)
            self.assertNotEqual(store_module.encode(replace(loaded_issue, title='Changed')), expected_issue)
            self.assertNotEqual(store_module.encode(replace(loaded_view, snapshot=b'changed PNG')), expected_view)
            self.assertNotEqual(store_module.encode(replace(loaded_view, markup_path='/Different')), expected_view)
            self.assertEqual(sdk.service.stage.GetRootLayer().ExportToString(), before)

    async def test_creation_stages_until_save_and_reveals_saved_issue(self):
        with controller_sdk(self) as sdk:
            draft = await self.create(sdk)
            self.assertEqual(sdk.service.list_issues(), ())
            self.assertIsNotNone(sdk.extension._annotation)
            draft.update(title=' Door ', description='Clearance')
            issue_id = await sdk.extension.save_details()
            saved = sdk.service.get_issue(issue_id)
            self.assertEqual(saved.title, 'Door')
            self.assertEqual(sdk.service.store.get_viewpoint(saved.initial_viewpoint_id).snapshot, b'accepted')
            self.assertIn('clear filters', sdk.calls)
            self.assertIsNone(sdk.extension._session)
            self.assertEqual(sdk.discarded, [])

    async def test_validation_stale_scene_and_commit_failure_keep_draft(self):
        for failure in ('title', 'long title', 'scene', 'commit', 'readonly'):
            with self.subTest(failure=failure), controller_sdk(self) as sdk:
                draft = await self.create(sdk)
                draft.update(title='' if failure=='title' else 'x'*256 if failure=='long title' else 'Door')
                if failure=='scene': sdk.service.generation += 1
                if failure=='commit': sdk.service.commit_session=lambda session: (_ for _ in ()).throw(ValueError('Commit failed'))
                if failure=='readonly': sdk.service.stage.GetRootLayer().SetPermissionToEdit(False)
                self.assertIsNone(await sdk.extension.save_details())
                self.assertIs(sdk.extension._session, draft)
                self.assertTrue(sdk.extension._details.error)
                self.assertFalse(sdk.extension._details.busy)
                self.assertEqual(sdk.service.list_issues(), ())
                self.assertFalse(sdk.discarded)
                sdk.service.stage.GetRootLayer().SetPermissionToEdit(True)

    async def test_cancel_after_capture_discards_only_owned_evidence(self):
        with controller_sdk(self) as sdk:
            await self.create(sdk)
            view = sdk.extension._session.viewpoint
            self.assertTrue(await sdk.extension.cancel_details('discard'))
            self.assertEqual(sdk.discarded, [view])
            self.assertIsNone(sdk.extension._details)
            self.assertEqual(sdk.service.list_issues(), ())

    async def test_cancel_placement_leaves_no_draft(self):
        with controller_sdk(self) as sdk:
            self.assertIsNone(await sdk.extension.begin_creation())
            self.assertIsNone(sdk.extension._session)
            self.assertEqual(sdk.calls, [('placement', True), ('placement', False)])

    async def test_saved_annotation_uses_copy_and_discard_preserves_original(self):
        with controller_sdk(self) as sdk:
            original = sdk.api.create(sdk.service, None, 'Default', sdk.view)
            original.update(title='Original')
            issue_id = sdk.service.commit_session(original)
            await sdk.extension.select_issue(issue_id)
            await sdk.extension.annotate_details()
            self.assertNotEqual(sdk.extension._session.viewpoint.id, sdk.view.id)
            self.assertIn(('copy', sdk.view.id), sdk.calls)
            await sdk.extension.cancel_details('discard')
            self.assertEqual(sdk.service.store.get_viewpoint(sdk.view.id), sdk.view)
            self.assertTrue(all(v.id != sdk.view.id for v in sdk.discarded))

    async def test_replacement_failure_and_repeated_replacement_preserve_last_accepted_draft(self):
        with controller_sdk(self) as sdk:
            await self.create(sdk)
            await sdk.extension.replace_screenshot()
            previous = sdk.extension._session.viewpoint
            async def fail(): raise ValueError('Capture failed')
            capture = sdk.markup.capture_viewpoint
            sdk.markup.capture_viewpoint = fail
            await sdk.extension.replace_screenshot()
            self.assertEqual(sdk.extension._session.viewpoint, previous)
            self.assertTrue(sdk.extension._details.error)
            sdk.markup.capture_viewpoint = capture
            await sdk.extension.replace_screenshot()
            self.assertIn(previous, sdk.discarded)
            sdk.extension._session.update(title='Accepted')
            accepted = sdk.extension._session.viewpoint
            issue_id = await sdk.extension.save_details()
            self.assertEqual(len(sdk.service.list_issues()), 1)
            self.assertEqual(sdk.service.get_issue(issue_id).initial_viewpoint_id, accepted.id)
            self.assertEqual(sdk.service.store.get_viewpoint(accepted.id).snapshot, accepted.snapshot)
            for superseded in sdk.discarded:
                with self.assertRaises(KeyError):
                    sdk.service.store.get_viewpoint(superseded.id)

    async def test_dirty_switch_stay_failed_save_discard_and_save(self):
        for decision in ('stay', 'save', 'discard', 'valid save'):
            with self.subTest(decision=decision), controller_sdk(self) as sdk:
                target = sdk.api.create(sdk.service, None, 'Default', None)
                target.update(title='Target')
                target_id = sdk.service.commit_session(target)
                draft = await self.create(sdk)
                if decision=='valid save': draft.update(title='New')
                result = await sdk.extension.select_issue(target_id, decision='save' if decision=='valid save' else decision)
                if decision in ('stay','save'):
                    self.assertIs(sdk.extension._session, draft)
                    self.assertIsNone(result)
                else:
                    self.assertEqual(sdk.extension._session.record.id, target_id)
                    self.assertEqual(len(sdk.service.list_issues()), 2 if decision=='valid save' else 1)

    async def test_cancel_during_capture_waits_for_native_drain(self):
        with controller_sdk(self) as sdk:
            started, drain = asyncio.Event(), asyncio.Event()
            async def capture():
                started.set()
                try: await asyncio.Future()
                except asyncio.CancelledError:
                    await drain.wait()
                    sdk.calls.append('drained')
                    raise
            sdk.markup.capture_viewpoint = capture
            task = sdk.extension._dispatch(sdk.extension._create_issue_from_pin, None)
            await started.wait()
            cancel = asyncio.create_task(sdk.extension.cancel_details('discard'))
            await asyncio.sleep(0)
            self.assertFalse(cancel.done())
            self.assertIsNotNone(sdk.extension._details)
            drain.set()
            await cancel
            self.assertTrue(task.done())
            self.assertIsNone(sdk.extension._session)

    async def test_shutdown_drains_capture_before_native_teardown(self):
        with controller_sdk(self) as sdk:
            started, drain = asyncio.Event(), asyncio.Event()
            async def capture():
                started.set()
                try: await asyncio.Future()
                except asyncio.CancelledError:
                    await drain.wait()
                    sdk.calls.append('drained')
                    raise
            sdk.markup.capture_viewpoint = capture
            sdk.extension._dispatch(sdk.extension._create_issue_from_pin, None)
            await started.wait()
            sdk.extension.on_shutdown()
            await asyncio.sleep(0)
            self.assertNotIn('markup destroyed', sdk.calls)
            drain.set()
            await sdk.extension._shutdown_task
            self.assertLess(sdk.calls.index('drained'), sdk.calls.index('markup destroyed'))

    async def test_failed_annotation_snapshot_cannot_commit_old_snapshot_on_retry(self):
        with controller_sdk(self) as sdk:
            await self.create(sdk)
            sdk.extension._session.update(title='Door')
            finish = sdk.markup.finish
            async def fail(*args, **kwargs): raise ValueError('Screenshot failed')
            sdk.markup.finish = fail
            self.assertIsNone(await sdk.extension.save_details())
            self.assertEqual(sdk.service.list_issues(), ())
            sdk.markup.finish = finish
            issue_id = await sdk.extension.save_details()
            saved = sdk.service.get_issue(issue_id)
            self.assertEqual(sdk.service.store.get_viewpoint(saved.initial_viewpoint_id).snapshot, b'accepted')

    async def test_failed_initial_capture_cannot_save_without_evidence(self):
        with controller_sdk(self) as sdk:
            async def fail(): raise ValueError('Capture failed')
            sdk.markup.capture_viewpoint = fail
            await self.create(sdk)
            sdk.extension._session.update(title='Door')
            self.assertIsNone(await sdk.extension.save_details())
            self.assertEqual(sdk.service.list_issues(), ())
            self.assertIsNotNone(sdk.extension._details)

    async def test_stale_saved_record_rejects_save_and_retains_editor(self):
        with controller_sdk(self) as sdk:
            draft = sdk.api.create(sdk.service, None, 'Default', None)
            draft.update(title='Original')
            issue_id = sdk.service.commit_session(draft)
            await sdk.extension.select_issue(issue_id)
            sdk.extension._session.update(title='Pending')
            sdk.service.set_status(issue_id, sdk.model.Status.RESOLVED)
            self.assertIsNone(await sdk.extension.save_details())
            self.assertIn('changed', sdk.extension._details.error)
            self.assertEqual(sdk.service.get_issue(issue_id).title, 'Original')

    async def test_cancel_during_annotation_snapshot_drains_before_discard(self):
        with controller_sdk(self) as sdk:
            await self.create(sdk)
            sdk.extension._session.update(title='Door')
            started, drain = asyncio.Event(), asyncio.Event()
            async def finish(record, save=True):
                started.set()
                await drain.wait()
                return replace(record, snapshot=b'accepted')
            sdk.markup.finish = finish
            saving = sdk.extension._dispatch(sdk.extension.save_details)
            await started.wait()
            cancelling = asyncio.create_task(sdk.extension.cancel_details('discard'))
            await asyncio.sleep(0)
            self.assertFalse(cancelling.done())
            self.assertFalse(sdk.discarded)
            drain.set()
            await cancelling
            self.assertEqual(sdk.service.list_issues(), ())
            self.assertTrue(sdk.discarded)
            self.assertTrue(saving.done())

    async def test_clean_screenshot_hiding_does_not_dispatch_user_close(self):
        with controller_sdk(self) as sdk:
            await self.create(sdk)
            callbacks = []
            details = sdk.extension._details
            details._visibility = lambda value: callbacks.append(value)
            window = types.SimpleNamespace(callback=details._visibility)
            window.set_visibility_changed_fn = lambda value: setattr(window, 'callback', value)
            details.window = window
            async def finish(record, save=True):
                with sdk.extension._evidence_ui((window,)):
                    self.assertIsNone(window.callback)
                with sdk.extension._evidence_ui(()):
                    self.assertIs(window.callback, details._visibility)
                return replace(record, snapshot=b'accepted')
            sdk.markup.finish = finish
            await sdk.extension.replace_screenshot()
            self.assertIs(window.callback, details._visibility)
            self.assertEqual(callbacks, [])

    async def test_discard_stale_annotation_closes_without_touching_replacement_scene(self):
        with controller_sdk(self) as sdk:
            await self.create(sdk)
            sdk.service.generation += 1
            async def finish(*args, **kwargs): raise ValueError('The annotation scene changed.')
            sdk.markup.finish = finish
            self.assertTrue(await sdk.extension.cancel_details('discard'))
            self.assertIsNone(sdk.extension._session)
            self.assertEqual(sdk.service.list_issues(), ())

    async def test_pin_filter_invalidates_saved_pins_without_disarming_placement(self):
        from test_lifecycle import lifecycle_sdk
        with lifecycle_sdk() as sdk:
            stage = object()
            service = types.SimpleNamespace(stage=stage, list_issues=lambda: (
                types.SimpleNamespace(id='first', anchor=object(), status='Open'),
                types.SimpleNamespace(id='second', anchor=object(), status='Closed')))
            adapter = sdk.viewport.ViewportAdapter(service)
            api = types.SimpleNamespace(stage=stage)
            adapter.clipping_planes = lambda viewport: ()
            adapter._placement = asyncio.get_running_loop().create_future()
            adapter._placement_viewport = api
            item = sdk.viewport._ViewportItem.__new__(sdk.viewport._ViewportItem)
            item.adapter, item.viewport_api = adapter, api
            item._computed = item._signature = None
            item.manipulator = types.SimpleNamespace(invalidate=lambda: None)
            with patch.object(sdk.viewport, 'world_anchor', return_value=(0, 0, 0)), patch.object(sdk.viewport, 'pin_is_visible', return_value=True):
                item.sync()
                self.assertEqual(item.visible_issue_ids, ('first', 'second'))
                adapter.filtered_issue_ids = frozenset({'second'})
                item.sync()
                self.assertEqual(item.visible_issue_ids, ('second',))
                adapter.filtered_issue_ids = frozenset()
                item.sync()
                self.assertEqual(item.visible_issue_ids, ())
                self.assertIs(item._signature[2], adapter._placement)
                self.assertFalse(adapter._placement.done())
                adapter.filtered_issue_ids = None
                item.sync()
                self.assertEqual(item.visible_issue_ids, ('first', 'second'))
            adapter._placement.cancel()

    async def test_related_and_reattach_stage_until_save_preserving_initial_view(self):
        with controller_sdk(self) as sdk:
            sdk.service.stage.DefinePrim('/Original', 'Cube')
            sdk.service.stage.DefinePrim('/Other', 'Cube')
            elements = importlib.import_module(sdk.service.__class__.__module__.rsplit('.', 1)[0] + '.elements')
            anchor = elements.make_anchor(sdk.service.stage, '/Original', (0, 0, 0))
            replacement = elements.make_anchor(sdk.service.stage, '/Other', (1, 0, 0))
            draft = sdk.api.create(sdk.service, anchor, 'Default', sdk.view)
            draft.update(title='Repair')
            issue_id = sdk.service.commit_session(draft)
            original = sdk.service.get_issue(issue_id)
            sdk.service._context.get_selection = lambda: types.SimpleNamespace(get_selected_prim_paths=lambda: ['/Other'])
            focused = []
            sdk.viewport.focus = focused.append
            await sdk.extension.select_issue(issue_id)
            await sdk.extension.add_selected_related()
            self.assertEqual(sdk.extension._session.record.anchor, anchor)
            await sdk.extension.remove_related(anchor.element)
            await sdk.extension.focus_related()
            self.assertEqual(focused, [(replacement.element,)])
            async def place(): return replacement
            sdk.viewport.request_placement = place
            await sdk.extension.reattach_pin()
            self.assertEqual(sdk.service.get_issue(issue_id), original)
            self.assertEqual(sdk.extension._session.record.anchor, replacement)
            await sdk.extension.cancel_details('discard')
            self.assertEqual(sdk.service.get_issue(issue_id), original)
            await sdk.extension.select_issue(issue_id)
            await sdk.extension.add_selected_related()
            await sdk.extension.reattach_pin()
            await sdk.extension.save_details()
            saved = sdk.service.get_issue(issue_id)
            self.assertEqual(saved.anchor, replacement)
            self.assertIn(replacement.element, saved.related_elements)
            self.assertEqual(saved.initial_viewpoint_id, sdk.view.id)

    async def test_comment_capture_annotate_and_add_are_staged_and_save_only_target_evidence(self):
        with controller_sdk(self) as sdk:
            draft = sdk.api.create(sdk.service, None, 'Default', sdk.view)
            draft.update(title='Original')
            issue_id = sdk.service.commit_session(draft)
            await sdk.extension.select_issue(issue_id)
            await sdk.extension.capture_comment_viewpoint()
            await sdk.extension.annotate_comment()
            sdk.extension._session.comment_text = 'Second angle'
            await sdk.extension.add_comment()
            accepted = sdk.extension._session.record.comments[-1]
            staged_view = sdk.extension._session.comment_viewpoints[accepted.id]
            self.assertEqual(staged_view.snapshot, b'accepted')
            self.assertEqual(sdk.service.get_issue(issue_id).comments, ())
            await sdk.extension.save_details()
            saved = sdk.service.get_issue(issue_id)
            self.assertEqual(saved.initial_viewpoint_id, sdk.view.id)
            self.assertEqual(saved.comments[-1].viewpoint_id, staged_view.id)
            self.assertEqual(sdk.service.store.get_viewpoint(staged_view.id), staged_view)
            self.assertEqual(sdk.service.store.get_viewpoint(sdk.view.id), sdk.view)
            self.assertFalse(any(v.id == staged_view.id for v in sdk.discarded))

    async def test_edit_saved_comment_evidence_copy_discard_then_save(self):
        with controller_sdk(self) as sdk:
            draft = sdk.api.create(sdk.service, None, 'Default', sdk.view)
            draft.update(title='Original')
            issue_id = sdk.service.commit_session(draft)
            await sdk.extension.select_issue(issue_id)
            await sdk.extension.capture_comment_viewpoint()
            sdk.extension._session.comment_text = 'Evidence'
            await sdk.extension.save_details()
            original = sdk.service.get_issue(issue_id)
            comment = original.comments[-1]
            saved_view = sdk.service.store.get_viewpoint(comment.viewpoint_id)
            for decision in ('discard', 'save'):
                await sdk.extension.select_issue(issue_id)
                await sdk.extension.annotate_comment(comment.id)
                copied = sdk.extension._session.comment_viewpoints[comment.id]
                self.assertNotEqual(copied.id, saved_view.id)
                if decision == 'discard':
                    await sdk.extension.cancel_details('discard')
                    self.assertEqual(sdk.service.get_issue(issue_id), original)
                else:
                    await sdk.extension.save_details()
                    updated = sdk.service.get_issue(issue_id)
                    self.assertEqual(updated.comments[-1].viewpoint_id, copied.id)
                    self.assertEqual(sdk.service.store.get_viewpoint(copied.id).snapshot, b'accepted')
                    self.assertEqual(updated.initial_viewpoint_id, sdk.view.id)
                self.assertEqual(sdk.service.store.get_viewpoint(saved_view.id), saved_view)
                self.assertEqual(sdk.service.store.get_viewpoint(sdk.view.id), sdk.view)

    async def test_comment_capture_requires_text_and_failed_commit_retains_all_evidence(self):
        with controller_sdk(self) as sdk:
            await self.create(sdk)
            sdk.extension._session.update(title='Original')
            await sdk.extension.capture_comment_viewpoint()
            pending = sdk.extension._session.comment_viewpoint
            self.assertIsNone(await sdk.extension.save_details())
            self.assertEqual(sdk.service.list_issues(), ())
            sdk.extension._session.comment_text = 'Pending'
            sdk.service.stage.GetRootLayer().SetPermissionToEdit(False)
            self.assertIsNone(await sdk.extension.save_details())
            self.assertIs(sdk.extension._session.comment_viewpoint, pending)
            sdk.service.stage.GetRootLayer().SetPermissionToEdit(True)
            await sdk.extension.cancel_details('discard')
            self.assertIn(pending, sdk.discarded)

    async def test_cancel_reattach_preserves_saved_anchor_and_current_draft(self):
        with controller_sdk(self) as sdk:
            draft = sdk.api.create(sdk.service, None, 'Default', sdk.view)
            draft.update(title='Original')
            issue_id = sdk.service.commit_session(draft)
            await sdk.extension.select_issue(issue_id)
            session = sdk.extension._session
            session.update(description='Keep pending text')
            started = asyncio.Event()
            async def place():
                started.set()
                await asyncio.Future()
            sdk.viewport.request_placement = place
            task = sdk.extension._dispatch(sdk.extension.reattach_pin)
            await started.wait()
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            self.assertIs(sdk.extension._session, session)
            self.assertEqual(session.record.description, 'Keep pending text')
            self.assertIsNone(session.record.anchor)
            self.assertEqual(sdk.calls[-1], ('placement', False))
            self.assertFalse(sdk.extension._details.busy)

    async def test_comment_replacement_failure_preserves_pending_then_discard_preserves_initial(self):
        with controller_sdk(self) as sdk:
            draft = sdk.api.create(sdk.service, None, 'Default', sdk.view)
            draft.update(title='Original')
            issue_id = sdk.service.commit_session(draft)
            await sdk.extension.select_issue(issue_id)
            await sdk.extension.capture_comment_viewpoint()
            pending = sdk.extension._session.comment_viewpoint
            async def fail(): raise ValueError('Capture failed')
            sdk.markup.capture_viewpoint = fail
            await sdk.extension.capture_comment_viewpoint()
            self.assertIs(sdk.extension._session.comment_viewpoint, pending)
            self.assertTrue(sdk.extension._details.error)
            await sdk.extension.cancel_details('discard')
            self.assertIn(pending, sdk.discarded)
            self.assertEqual(sdk.service.store.get_viewpoint(sdk.view.id), sdk.view)
            self.assertEqual(sdk.service.get_issue(issue_id).comments, ())


class NativeCallbackDispatchTests(unittest.TestCase):
    def setUp(self):
        try:
            self.previous_loop = asyncio.get_event_loop()
        except RuntimeError:
            self.previous_loop = None
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        tasks = asyncio.all_tasks(self.loop)
        for task in tasks:
            task.cancel()
        if tasks:
            self.loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        self.loop.close()
        asyncio.set_event_loop(self.previous_loop)

    def test_native_create_click_schedules_on_installed_loop_between_ticks(self):
        import gc
        import warnings
        from test_acc_ui import panel_types
        with controller_sdk(self) as sdk, warnings.catch_warnings(record=True) as warnings_seen:
            warnings.simplefilter('always')
            List, _ = panel_types()
            panel = List(sdk.service, on_select=sdk.extension.select_issue,
                         on_create=sdk.extension.begin_creation, on_error=sdk.extension._dispatch)
            sdk.extension._window = panel
            placement = self.loop.create_future()
            async def place(): return await placement
            sdk.viewport.request_placement = place
            sdk.viewport.cancel_placement = placement.cancel
            try:
                with self.assertRaises(RuntimeError): asyncio.get_running_loop()
                panel._create()
                self.assertEqual(len(sdk.extension._tasks), 1)
                self.loop.run_until_complete(asyncio.sleep(0))
                self.assertTrue(panel._placing)
                panel._cancel_placement()
                self.loop.run_until_complete(asyncio.sleep(0))
                self.assertFalse(panel._placing)
                self.assertFalse(sdk.extension._tasks)
                self.assertEqual(sdk.service.list_issues(), ())
                gc.collect()
                self.assertFalse([warning for warning in warnings_seen if 'never awaited' in str(warning.message)])
            finally:
                placement.cancel()
                panel.destroy()

    def test_scheduling_rejection_closes_both_coroutines_and_shows_error(self):
        import inspect
        import warnings
        with controller_sdk(self) as sdk, warnings.catch_warnings(record=True) as warnings_seen:
            warnings.simplefilter('always')
            async def action(): return 'result'
            result = action()
            wrappers = []
            def reject(coroutine, **kwargs):
                wrappers.append(coroutine)
                raise RuntimeError('Scheduler rejected the action')
            try:
                with patch.object(self.loop, 'create_task', side_effect=reject):
                    self.assertIsNone(sdk.extension._dispatch(lambda: result))
                self.assertEqual(len(wrappers), 1)
                self.assertEqual(inspect.getcoroutinestate(wrappers[0]), inspect.CORO_CLOSED)
                self.assertEqual(inspect.getcoroutinestate(result), inspect.CORO_CLOSED)
                self.assertIn('Scheduler rejected', sdk.extension._window._error)
                self.assertFalse(sdk.extension._tasks)
                self.assertFalse([warning for warning in warnings_seen if 'never awaited' in str(warning.message)])
            finally:
                result.close()
                for wrapper in wrappers:
                    wrapper.close()

    def test_synchronous_manager_shutdown_schedules_drain_on_pending_owner_loop(self):
        with controller_sdk(self) as sdk:
            completion = self.loop.create_future()
            async def capture():
                try:
                    await asyncio.Future()
                except asyncio.CancelledError:
                    await completion
                    sdk.calls.append('drained')
                    raise
            async def start():
                task = sdk.extension._dispatch(lambda: sdk.extension._operation(capture))
                await asyncio.sleep(0)
                return task
            task = self.loop.run_until_complete(start())
            try:
                with self.assertRaises(RuntimeError): asyncio.get_running_loop()
                sdk.extension.on_shutdown()
                self.assertFalse(sdk.extension._shutdown_task.done())
                self.assertNotIn('markup destroyed', sdk.calls)
                completion.set_result(None)
                self.loop.run_until_complete(sdk.extension._shutdown_task)
                self.assertLess(sdk.calls.index('drained'), sdk.calls.index('markup destroyed'))
                self.assertTrue(task.done())
            finally:
                if not completion.done(): completion.set_result(None)
                self.loop.run_until_complete(asyncio.gather(task, return_exceptions=True))
