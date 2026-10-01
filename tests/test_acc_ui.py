"""Native UI boundary doubles exercise real panel code without a Kit process."""

import ast
import asyncio
from enum import Enum
from io import BytesIO
import inspect
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
import weakref
from unittest.mock import patch


class Status(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class ValueModel:
    def __init__(self, value):
        self.value = value
        self.callbacks = []

    @property
    def as_string(self):
        return str(self.value)

    @property
    def as_int(self):
        return int(self.value)

    def set_value(self, value):
        self.value = value
        for callback in tuple(self.callbacks):
            callback(self)

    def add_value_changed_fn(self, callback):
        self.callbacks.append(callback)
        return callback

    def remove_value_changed_fn(self, callback):
        self.callbacks.remove(callback)


class Widget:
    widgets = []
    containers = []

    def __init__(self, *args, **kwargs):
        self.args = args
        self.__dict__.update(kwargs)
        self.enabled = kwargs.get("enabled", True)
        self.visible = True
        self.docked = False
        self.parent = self.containers[-1] if self.containers else None
        self.kind = type(self).__name__
        self.frame = self
        self.visibility_callback = None
        self.build_count = 0
        self.destroy_calls = 0
        self.computed_width = self.computed_height = 0
        self.dock_calls = []
        self.widgets.append(self)

    def __enter__(self):
        self.containers.append(self)
        return self

    def __exit__(self, *args):
        self.containers.pop()

    def set_build_fn(self, callback):
        self.build = callback

    def rebuild(self):
        assert not self.destroy_calls, "Released frame was rebuilt"
        self.build_count += 1
        self.build()

    def set_visibility_changed_fn(self, callback):
        self.visibility_callback = callback

    def destroy(self):
        assert self.visibility_callback is None, "Detach callbacks before native destruction"
        self.destroy_calls += 1

    def deferred_dock_in(self, *args, **kwargs):
        self.docking = (args, kwargs)

    def dock_in(self, viewport, side, fraction):
        assert not self.destroy_calls, "Released window was docked"
        assert self.visible, "Capture-hidden window was docked"
        assert self.computed_width > 0 and self.computed_height > 0, "Native window is not ready before an update"
        self.dock_calls.append((viewport, side, fraction))
        self.docking = (side, fraction)
        self.docked = True


class UpdateStream:
    def __init__(self):
        self.subscriptions = weakref.WeakSet()
        self.viewport = object()

    def create_subscription_to_pop(self, callback, **kwargs):
        class Subscription:
            pass
        subscription = Subscription()
        subscription.callback = callback
        self.subscriptions.add(subscription)
        return subscription

    def emit(self, *, render=True):
        if render:
            for widget in Widget.widgets:
                if widget.kind == 'Window' and widget.visible and not widget.destroy_calls:
                    widget.computed_width, widget.computed_height = 300, 600
        for subscription in tuple(self.subscriptions):
            subscription.callback(None)


class FillPolicy(Enum):
    PRESERVE_ASPECT_FIT = 1


class IwpFillPolicy(Enum):
    IWP_PRESERVE_ASPECT_FIT = 1


class ImageWithProvider(Widget):
    # omni.ui 3.2.5 _ui.pyi:5014: this binding accepts IwpFillPolicy, not Image's FillPolicy.
    def __init__(self, provider, *, fill_policy, **kwargs):
        if not isinstance(fill_policy, IwpFillPolicy):
            raise TypeError('ImageWithProvider.fill_policy requires IwpFillPolicy')
        super().__init__(provider, fill_policy=fill_policy, **kwargs)


class ComboModel:
    def __init__(self, selected):
        self.selection = ValueModel(selected)
        self.callbacks = []

    def get_item_value_model(self, *args):
        return self.selection

    def add_item_changed_fn(self, callback):
        self.callbacks.append(callback)
        return callback

    def remove_item_changed_fn(self, callback):
        self.callbacks.remove(callback)

    def choose(self, index):
        self.selection.set_value(index)
        for callback in tuple(self.callbacks):
            callback(self, None)


class Combo(Widget):
    def __init__(self, selected, *items, **kwargs):
        super().__init__(selected, *items, **kwargs)
        self.model = ComboModel(selected)


def panel_types(updates=None):
    updates = updates if updates is not None else UpdateStream()
    path = Path(__file__).resolve().parent.parent / "issues_tag/window.py"
    source = ast.parse(path.read_text(encoding="utf-8"), str(path))
    definitions = [node for node in source.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))]
    names = {node.name for node in definitions}
    assert "IssueDetailsWindow" in names, "Separate staged IssueDetailsWindow is missing"
    widgets = {name: type(name, (Widget,), {}) for name in ("Window", "ScrollingFrame", "VStack", "HStack", "Label", "Button", "StringField", "Separator", "Spacer")}
    ui = SimpleNamespace(**widgets, ImageWithProvider=ImageWithProvider, SimpleStringModel=ValueModel, ComboBox=Combo,
                         DockPolicy=SimpleNamespace(DO_NOTHING=0),
                         DockPosition=SimpleNamespace(LEFT=0, RIGHT=1),
                         Workspace=SimpleNamespace(get_window=lambda name: updates.viewport),
                         FillPolicy=FillPolicy, IwpFillPolicy=IwpFillPolicy)
    app = SimpleNamespace(get_app=lambda: SimpleNamespace(get_update_event_stream=lambda: updates))
    namespace = {"asyncio": asyncio, "inspect": inspect, "ui": ui, "Status": Status,
                 "omni": SimpleNamespace(kit=SimpleNamespace(app=app)),
                 "STYLE": {}, "ACCENT": 0, "BytesIO": BytesIO, "attachment_state": lambda *a: "verified",
                 "resolve_element": lambda *a: SimpleNamespace(state="resolved")}
    exec(compile(ast.Module(body=definitions, type_ignores=[]), str(path), "exec"), namespace)
    return namespace["IssuesWindow"], namespace["IssueDetailsWindow"]


def record(issue_id, number, title, description="", status=Status.OPEN, issue_type="Default", comments=()):
    return SimpleNamespace(id=issue_id, number=number, title=title, description=description,
                           status=status, issue_type=issue_type, author="Reviewer", created_at="2026-10-01",
                           modified_at="2026-10-01", anchor=None, related_elements=(), initial_viewpoint_id="", comments=comments)


class Service:
    def __init__(self):
        self.stage = object()
        self.author_name = "Reviewer"
        self.is_dirty = False
        self.viewport = SimpleNamespace(filtered_issue_ids=None)
        self.records = [record("b", 12, "Door swing", "Touches WALL", issue_type="Coordination"),
                        record("z", 2, "Roof", status=Status.RESOLVED),
                        record("a", 2, "Window", "seal missing")]
        self.listeners = []

    @property
    def author_name(self):
        return self._author_name

    @author_name.setter
    def author_name(self, value):
        value = value.strip()
        if not value:
            raise ValueError("Enter an author name.")
        self._author_name = value

    def add_listener(self, callback):
        self.listeners.append(callback)

    def remove_listener(self, callback):
        self.listeners.remove(callback)

    def list_issues(self):
        return tuple(self.records)

    def list_types(self):
        return ("Default", "Coordination")


class Session:
    def __init__(self):
        self.record = record("draft", 0, "Draft title", "Draft description")
        self.viewpoint = None
        self.comment_text = ""
        self.comment_viewpoint = None
        self.comment_viewpoints = {}
        self.stage = object()
        self.is_new = True
        self.dirty = False

    def update(self, **fields):
        self.record = SimpleNamespace(**{**vars(self.record), **fields})
        self.dirty = True


class ACCUITests(unittest.TestCase):
    def setUp(self):
        Widget.widgets = []
        Widget.containers = []
        self.updates = UpdateStream()
        self.List, self.Details = panel_types(self.updates)
        self.service = Service()
        self.events = []
        self.panels = []

    def tearDown(self):
        for panel in self.panels:
            panel.destroy()

    def list_panel(self, **callbacks):
        panel = self.List(self.service, on_select=lambda issue_id: self.events.append(("select", issue_id)),
                          on_create=lambda: self.events.append("create"), **callbacks)
        self.panels.append(panel)
        return panel

    def details_panel(self):
        self.session = Session()
        panel = self.Details(self.session, ("Default", "Coordination"),
                             on_save=lambda: self.events.append("save"),
                             on_cancel=lambda: self.events.append("cancel"),
                             on_annotate=lambda: self.events.append("annotate"),
                             on_replace=lambda: self.events.append("replace"),
                             on_comment_view=lambda value: self.events.append(("view", value)),
                             on_reattach=lambda: self.events.append('reattach'),
                             on_add_related=lambda: self.events.append('add related'),
                             on_remove_related=lambda ref: self.events.append(('remove related', ref)),
                             on_focus_related=lambda: self.events.append('focus related'),
                             on_capture_comment=lambda: self.events.append('capture comment'),
                             on_annotate_comment=lambda comment_id=None: self.events.append(('annotate comment', comment_id)),
                             on_add_comment=lambda: self.events.append('add comment'))
        self.panels.append(panel)
        return panel

    def click(self, text):
        widget = next(w for w in reversed(Widget.widgets) if w.args and w.args[0] == text and hasattr(w, "clicked_fn"))
        widget.clicked_fn()
        return widget

    def test_search_matches_number_title_and_description_without_case(self):
        panel = self.list_panel()
        for search in ("12", "DOOR", "wall"):
            panel.search.set_value(search)
            self.assertEqual([r.id for r in panel.filtered_records()], ["b"])

    def test_status_type_filters_and_stable_number_identity_order(self):
        panel = self.list_panel()
        self.assertEqual([r.id for r in panel.filtered_records()], ["a", "z", "b"])
        panel.status_filter = Status.OPEN.value
        panel.type_filter = "Coordination"
        panel.refresh()
        self.assertEqual(panel.visible_issue_ids, frozenset({"b"}))
        self.assertEqual(self.service.viewport.filtered_issue_ids, frozenset({"b"}))
        self.assertEqual(len(self.service.records), 3)

    def test_clear_filters_makes_new_saved_issue_discoverable(self):
        panel = self.list_panel()
        panel.search.set_value("absent")
        panel.status_filter = Status.CLOSED.value
        panel.type_filter = "Coordination"
        panel.clear_filters()
        self.assertEqual(len(panel.filtered_records()), 3)
        self.assertEqual(self.service.viewport.filtered_issue_ids, frozenset({"a", "b", "z"}))

    def test_create_and_select_only_delegate_to_owner(self):
        panel = self.list_panel()
        self.click("Create issue")
        panel.select_issue("b")
        self.assertEqual(self.events, ["create", ("select", "b")])
        self.assertEqual(self.service.records[0].title, "Door swing")

    def test_hidden_list_updates_pin_filter_without_rebuilding_native_frame(self):
        panel = self.list_panel()
        panel.window.visible = False
        count = panel.window.build_count
        panel.search.set_value("roof")
        panel.refresh()
        self.assertEqual(panel.window.build_count, count)
        self.assertEqual(self.service.viewport.filtered_issue_ids, frozenset({"z"}))
        panel.show()
        self.assertGreater(panel.window.build_count, count)

    def test_destroy_removes_listener_and_neutralizes_retained_callbacks(self):
        panel = self.list_panel()
        callback = next(w.clicked_fn for w in Widget.widgets if w.args and w.args[0] == "Create issue")
        native = panel.window
        panel.destroy()
        panel.refresh()
        callback()
        panel.search.set_value("roof")
        self.assertFalse(self.events)
        self.assertFalse(self.service.listeners)
        self.assertEqual(native.destroy_calls, 1)

    def test_loading_error_is_visible_and_create_disabled(self):
        self.service.list_issues = lambda: (_ for _ in ()).throw(ValueError("Malformed issues"))
        panel = self.list_panel()
        self.assertEqual(panel.load_error, "Malformed issues")
        self.assertFalse(self.click("Create issue").enabled)
        self.assertFalse(self.events)

    def test_loading_error_with_selected_project_type_builds_and_recovers(self):
        for failing_method in ("list_issues", "list_types"):
            with self.subTest(failing_method=failing_method):
                panel = self.list_panel()
                type_combo = next(w for w in reversed(Widget.widgets) if isinstance(w, Combo) and "All types" in w.args)
                type_combo.model.choose(2)
                self.assertEqual(panel.type_filter, "Coordination")
                self.assertEqual(panel.visible_issue_ids, frozenset({"b"}))
                original = getattr(self.service, failing_method)
                setattr(self.service, failing_method, lambda: (_ for _ in ()).throw(ValueError("Malformed issues")))
                try:
                    try:
                        panel.refresh()
                    except ValueError as exc:
                        self.fail(f"Loading error escaped while building fallback controls: {exc}")
                    self.assertEqual(panel.load_error, "Malformed issues")
                    self.assertEqual(panel.type_filter, "All types")
                    self.assertEqual(panel.visible_issue_ids, frozenset())
                    self.assertFalse(self.click("Create issue").enabled)
                    self.assertTrue(any(w.args and w.args[0] == "Malformed issues" for w in Widget.widgets))
                    self.assertFalse(self.events)
                finally:
                    setattr(self.service, failing_method, original)
                panel.refresh()
                self.assertEqual(panel.load_error, "")
                self.assertEqual(panel.visible_issue_ids, frozenset({"a", "b", "z"}))
                self.assertEqual(self.service.viewport.filtered_issue_ids, panel.visible_issue_ids)
                type_combo = next(w for w in reversed(Widget.widgets) if isinstance(w, Combo) and "All types" in w.args)
                type_combo.model.choose(2)
                self.assertEqual(panel.visible_issue_ids, frozenset({"b"}))

    def test_acceptance_arrows_use_distinct_in_bounds_native_percent_rectangles(self):
        path = Path(__file__).with_name('test_acc_workflow.py')
        tree = ast.parse(path.read_text())
        definition = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == '_arrow')
        namespace = {}
        exec(compile(ast.Module(body=[definition], type_ignores=[]), str(path), 'exec'), namespace)
        rectangles = []
        core = SimpleNamespace(add_element=lambda *args, **kwargs: rectangles.append(args[:4]))
        extension = SimpleNamespace(_markup=SimpleNamespace(core=core))
        for offset in (0, 20, 30, 40, 60):
            namespace['_arrow'](extension, offset)
        self.assertEqual(len(set(rectangles)), len(rectangles))
        self.assertTrue(all(0 <= value <= 100 for rect in rectangles for value in rect), rectangles)
        self.assertTrue(all(x1 < x2 and y1 < y2 for x1, y1, x2, y2 in rectangles))

    def test_failed_native_png_validation_retains_exact_capture(self):
        import io
        import tempfile
        with patch.object(sys, 'path', [str(Path(__file__).resolve().parents[1] / 'verification/python'), *sys.path]):
            from PIL import Image
        path = Path(__file__).with_name('test_acc_workflow.py')
        tree = ast.parse(path.read_text())
        definition = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == '_png')
        image = Image.new('RGB', (128, 128))
        image.putdata([(0, index % 128, index % 256) for index in range(128 * 128)])
        output = io.BytesIO()
        image.save(output, format='PNG')
        data = output.getvalue()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'verification').mkdir()
            namespace = {'ROOT': root, 'io': io}
            exec(compile(ast.Module(body=[definition], type_ignores=[]), str(path), 'exec'), namespace)
            with self.assertRaisesRegex(AssertionError, 'Native red arrow is absent'):
                namespace['_png'](SimpleNamespace(snapshot=data), 'failed.png', True)
            self.assertEqual((root / 'verification' / 'failed.png').read_bytes(), data)

    def test_acceptance_click_preserves_panels_and_refinds_after_public_focus(self):
        path = Path(__file__).with_name('test_acc_workflow.py')
        tree = ast.parse(path.read_text())
        definition = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef) and node.name == '_button')
        for target in ('Issues', 'Unsaved issue changes'):
            with self.subTest(target=target):
                events = []
                panels = {name: SimpleNamespace(docked=True, visible=True) for name in ('Issues', 'Issue details')}
                panels['Unsaved issue changes'] = SimpleNamespace(docked=False, visible=True)
                async def focus():
                    events.append('focus')
                async def forbidden_click():
                    self.fail('WidgetRef.click undocks its window')
                old = SimpleNamespace(focus=focus, click=forbidden_click, center='stale center')
                fresh = SimpleNamespace(center='fresh center')
                def find(query):
                    events.append('find')
                    return fresh if 'focus' in events else old
                async def click(center):
                    self.assertEqual(center, 'fresh center')
                    events.append('native click')
                async def wait(*args):
                    pass
                ui = SimpleNamespace(Workspace=SimpleNamespace(get_window=panels.get))
                modules = {'omni': SimpleNamespace(ui=ui), 'omni.ui': ui,
                           'omni.kit.ui_test': SimpleNamespace(find=find, emulate_mouse_move_and_click=click)}
                namespace = {'frames': wait, 'asyncio': SimpleNamespace(sleep=wait)}
                exec(compile(ast.Module(body=[definition], type_ignores=[]), str(path), 'exec'), namespace)
                with patch.dict(sys.modules, modules):
                    asyncio.run(namespace['_button'](target, 'Action'))
                self.assertEqual(events, ['find', 'focus', 'find', 'native click'])
                self.assertTrue(panels['Issues'].docked and panels['Issue details'].docked)

    def test_review_button_dispatches_and_is_disabled_while_busy(self):
        panel = self.details_panel()
        panel.on_open_review_view = lambda: self.events.append('review')
        self.session.viewpoint = SimpleNamespace(id='initial', snapshot=b'')
        panel.refresh()
        self.assertTrue(self.click('Open review view').enabled)
        self.assertEqual(self.events, ['review'])
        panel.set_busy(True)
        self.assertFalse(self.click('Open review view').enabled)
        self.assertEqual(self.events, ['review'])
        panel.destroy()
        self.assertIsNone(panel.on_open_review_view)

    def test_dirty_guidance_updates_for_typing_without_rebuilding_or_replacing_fields(self):
        for field in ('title', 'description', 'comment'):
            with self.subTest(field=field):
                panel = self.details_panel()
                count = panel.window.build_count
                label = panel._draft_state
                self.assertEqual(label.text, 'No unsaved issue edits. Scene Save writes committed changes to disk.')
                model = getattr(panel, field)
                model.set_value('Unsaved text')
                self.assertEqual(label.text, 'Unsaved issue edits. Save issue, then save scene.')
                self.assertEqual(panel.window.build_count, count)
                self.assertIs(getattr(panel, field), model)
                panel.destroy()
                self.assertFalse(model.callbacks)

    def test_dirty_guidance_updates_for_status_type_and_evidence(self):
        for field, value in (('status', Status.CLOSED), ('issue_type', 'Coordination')):
            with self.subTest(field=field):
                panel = self.details_panel()
                count = panel.window.build_count
                panel._pick(ComboModel(0), (value,), field)
                self.assertEqual(panel._draft_state.text, 'Unsaved issue edits. Save issue, then save scene.')
                self.assertEqual(panel.window.build_count, count)
        panel = self.details_panel()
        self.session.viewpoint = SimpleNamespace(id='owned', snapshot=b'')
        self.session.dirty = True
        panel.set_busy(False)
        self.assertEqual(panel._draft_state.text, 'Unsaved issue edits. Save issue, then save scene.')

    def test_details_sync_updates_draft_fields_and_pending_comment_only(self):
        panel = self.details_panel()
        panel.title.set_value("Edited")
        panel.description.set_value("Changed draft")
        panel.comment.set_value("Pending investigation")
        panel.sync()
        self.assertEqual(self.session.record.title, "Edited")
        self.assertEqual(self.session.record.description, "Changed draft")
        self.assertEqual(self.session.comment_text, "Pending investigation")
        self.assertFalse(self.events)

    def test_save_and_cancel_delegate_and_save_syncs_before_callback(self):
        panel = self.details_panel()
        panel.title.set_value("Ready")
        self.click("Save")
        self.assertEqual(self.session.record.title, "Ready")
        self.click("Cancel")
        self.assertEqual(self.events, ["save", "cancel"])

    def test_native_close_delegates_without_destroying_session(self):
        panel = self.details_panel()
        panel.title.set_value("Unsaved")
        panel.window.visibility_callback(False)
        self.assertEqual(self.events, ["cancel"])
        self.assertEqual(self.session.record.title, "Unsaved")
        self.assertEqual(panel.window.destroy_calls, 0)
        self.assertTrue(panel.window.visible)

    def test_busy_blocks_save_capture_but_cancel_and_close_delegate(self):
        panel = self.details_panel()
        panel.set_busy(True)
        for text in ("Save", "Annotate screenshot", "Replace screenshot"):
            widget = self.click(text)
            self.assertFalse(widget.enabled, text)
        self.assertFalse(self.events)
        self.assertTrue(self.click("Cancel").enabled)
        panel.window.visibility_callback(False)
        self.assertEqual(self.events, ["cancel", "cancel"])
        self.assertTrue(panel.window.visible)
        self.events.clear()
        panel.set_busy(False)
        panel.set_error("Capture failed")
        self.assertTrue(any(w.args and w.args[0] == "Capture failed" for w in Widget.widgets))
        self.click("Save")
        self.assertEqual(self.events, ["save"])

    def test_refresh_preserves_typed_fields_and_type_selection_matches_items(self):
        panel = self.details_panel()
        panel.title.set_value("Uncommitted title")
        panel._issue_type = "Coordination"
        panel.types = ("Default", "Coordination", "Safety")
        panel.refresh()
        self.assertEqual(panel.title.as_string, "Uncommitted title")
        type_combo = next(w for w in reversed(Widget.widgets) if isinstance(w, Combo) and "Safety" in w.args)
        self.assertEqual(type_combo.args[type_combo.model.selection.as_int + 1], "Coordination")
        type_combo.model.choose(2)
        panel.sync()
        self.assertEqual(self.session.record.issue_type, "Safety")

    def test_history_view_and_capture_actions_only_delegate(self):
        panel = self.details_panel()
        self.session.record.comments = (SimpleNamespace(id="saved-comment", text="Saved comment", author="Reviewer", created_at="Today", viewpoint_id="old-view"),)
        panel.refresh()
        self.click("Open comment view")
        self.click("Replace screenshot")
        self.assertEqual(self.events, [("view", "old-view"), "replace"])

    def test_hidden_details_refresh_and_released_callbacks_are_safe(self):
        panel = self.details_panel()
        callback = next(w.clicked_fn for w in Widget.widgets if w.args and w.args[0] == "Save")
        native = panel.window
        native.visible = False
        count = native.build_count
        panel.refresh()
        self.assertEqual(native.build_count, count)
        panel.destroy()
        callback()
        panel.sync()
        panel.refresh()
        self.assertFalse(self.events)
        self.assertIsNone(native.visibility_callback)
        self.assertEqual(native.destroy_calls, 1)

    def test_panels_dock_on_opposite_sides_and_keep_save_outside_scroll(self):
        listing = self.list_panel()
        listing.show()
        details = self.details_panel()
        self.assertFalse(listing.window.docked)
        self.assertFalse(details.window.docked)
        self.updates.emit()
        self.assertEqual(listing.window.docking, (0, 0.23))
        self.assertEqual(details.window.docking, (1, 0.26))
        save = next(w for w in reversed(Widget.widgets) if w.args and w.args[0] == "Save")
        ancestors = []
        while save.parent:
            save = save.parent
            ancestors.append(save.kind)
        self.assertNotIn("ScrollingFrame", ancestors, "Save must stay visible below scrolling details")

    def test_docking_waits_for_native_geometry_and_viewport(self):
        listing = self.list_panel()
        listing.show()
        details = self.details_panel()
        self.updates.emit(render=False)
        self.assertFalse(listing.window.docked)
        self.assertFalse(details.window.docked)
        self.updates.viewport = None
        self.updates.emit()
        self.assertFalse(listing.window.docked)
        self.assertFalse(details.window.docked)
        self.updates.viewport = object()
        self.updates.emit()
        self.assertEqual(listing.window.docking, (0, .23))
        self.assertEqual(details.window.docking, (1, .26))
        self.assertFalse(self.updates.subscriptions)

    def test_capture_hidden_panels_dock_only_after_visibility_is_restored(self):
        listing = self.list_panel()
        listing.show()
        details = self.details_panel()
        panels = (listing, details)
        for panel in panels:
            panel.window.visible = False
        self.updates.emit()
        for panel in panels:
            self.assertFalse(panel.window.visible)
            self.assertFalse(panel.window.docked)
            panel.window.visible = True
        self.updates.emit()
        self.assertEqual(listing.window.docking, (0, .23))
        self.assertEqual(details.window.docking, (1, .26))
        self.assertFalse(self.events, 'Docking must not dispatch close or editing callbacks')

    def test_destroy_before_update_releases_docking_and_stale_callbacks_are_inert(self):
        listing = self.list_panel()
        listing.show()
        details = self.details_panel()
        callbacks = [subscription.callback for subscription in self.updates.subscriptions]
        self.assertEqual(len(callbacks), 2)
        natives = [panel.window for panel in (listing, details)]
        for panel in (listing, details):
            panel.destroy()
        self.assertFalse(self.updates.subscriptions)
        for callback in callbacks:
            callback(None)
        self.updates.emit()
        for native in natives:
            self.assertEqual(native.destroy_calls, 1)
            self.assertFalse(native.dock_calls)

    def test_repeated_show_keeps_one_pending_dock_and_does_not_redock(self):
        listing = self.list_panel()
        for _ in range(3):
            listing.show()
        self.assertEqual(len(self.updates.subscriptions), 1)
        self.updates.emit()
        listing.show()
        self.updates.emit()
        self.assertEqual(len(listing.window.dock_calls), 1)
        self.assertFalse(self.updates.subscriptions)

    def test_removed_type_retains_accurate_label_and_callback_values(self):
        panel = self.details_panel()
        panel._issue_type = "Coordination"
        panel.types = ("Default", "Safety")
        panel.refresh()
        combo = next(w for w in reversed(Widget.widgets) if isinstance(w, Combo) and "Safety" in w.args)
        self.assertEqual(combo.args[combo.model.selection.as_int + 1], "Coordination")
        combo.model.choose(1)
        panel.sync()
        self.assertEqual(self.session.record.issue_type, "Safety")

    def test_callback_failure_keeps_draft_and_shows_error(self):
        panel = self.details_panel()
        panel.on_save = lambda: (_ for _ in ()).throw(ValueError("Title required"))
        panel.title.set_value("Still editing")
        self.click("Save")
        self.assertEqual(panel._error, "Title required")
        self.assertEqual(self.session.record.title, "Still editing")
        self.assertTrue(panel.window.visible)

    def test_listener_cleanup_failure_still_releases_native_window(self):
        panel = self.list_panel()
        native = panel.window
        self.service.remove_listener = lambda callback: (_ for _ in ()).throw(RuntimeError("listener removal"))
        with self.assertRaises(ExceptionGroup):
            panel.destroy()
        self.assertEqual(native.destroy_calls, 1)
        self.assertIsNone(self.service.viewport.filtered_issue_ids)
        self.assertFalse(panel.search.callbacks)

    def test_screenshot_provider_reuses_decoded_evidence_and_releases_on_clear(self):
        panel = self.details_panel()
        opens = []

        class Image:
            format = "PNG"
            size = (2, 2)
            width = height = 2

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def thumbnail(self, size):
                pass

            def convert(self, mode):
                return self

            def tobytes(self):
                return bytes(range(16))

        def open_image(stream):
            opens.append(stream.read())
            return Image()

        class Provider:
            def set_bytes_data(self, pixels, size):
                self.pixels, self.size = pixels, size

        panel._snapshot.__globals__["ui"].ByteImageProvider = Provider
        self.session.viewpoint = SimpleNamespace(snapshot=b"saved PNG")
        with patch.dict(sys.modules, {"PIL": SimpleNamespace(Image=SimpleNamespace(open=open_image))}):
            panel.refresh()
            provider = panel._provider
            panel.set_error("Retry capture")
            self.assertIs(panel._provider, provider)
            self.assertEqual(opens, [b"saved PNG"])
            self.assertEqual(provider.size, [2, 2])
            self.session.viewpoint = None
            panel.refresh()
            self.assertIsNone(panel._provider)

    def test_status_and_type_combo_changes_stage_values_without_actions(self):
        panel = self.details_panel()
        status = next(w for w in reversed(Widget.widgets) if isinstance(w, Combo) and "Closed" in w.args)
        status.model.choose(3)
        self.assertEqual(self.session.record.status, Status.CLOSED)
        self.assertFalse(self.events)
        listing = self.list_panel()
        status_filter = next(w for w in reversed(Widget.widgets) if isinstance(w, Combo) and "All statuses" in w.args)
        status_filter.model.choose(3)
        self.assertEqual(listing.visible_issue_ids, frozenset({"z"}))

    def test_list_callbacks_use_owner_error_dispatcher(self):
        def dispatch(callback, *args):
            self.events.append("dispatch")
            return callback(*args)
        panel = self.list_panel(on_error=dispatch)
        panel.select_issue("b")
        self.assertEqual(self.events, ["dispatch", ("select", "b")])

    def test_author_setting_uses_owner_dispatcher_without_rewriting_saved_attribution(self):
        def dispatch(callback, *args):
            self.events.append("dispatch")
            return callback(*args)
        comment = SimpleNamespace(id="imported", author="Imported reviewer", created_at="Yesterday",
                                  text="Existing comment", viewpoint_id="")
        self.service.records[0].comments = (comment,)
        saved = [vars(item).copy() for item in self.service.records]
        self.service.author_name = "Current reviewer"
        panel = self.list_panel(on_error=dispatch)
        fields = [w for w in Widget.widgets if w.kind == "StringField" and w.args[0].as_string == "Current reviewer"]
        self.assertEqual(len(fields), 1, "Expose the configured author as an editable field")
        fields[0].args[0].set_value("  Next reviewer  ")
        self.click("Apply")
        self.assertEqual(self.events, ["dispatch"])
        self.assertEqual(self.service.author_name, "Next reviewer")
        self.assertEqual(fields[0].args[0].as_string, "Next reviewer")
        self.assertTrue(any(w.args and w.args[0] == "Current author: Next reviewer" for w in Widget.widgets))
        self.assertEqual([vars(item) for item in self.service.records], saved)
        self.assertEqual((comment.author, comment.created_at), ("Imported reviewer", "Yesterday"))
        apply = next(w for w in reversed(Widget.widgets) if w.args and w.args[0] == "Apply")
        ancestors = []
        while apply.parent:
            apply = apply.parent
            ancestors.append(apply.kind)
        self.assertNotIn("ScrollingFrame", ancestors, "Author configuration must stay reachable below the issue list")
        self.assertFalse(self.service.is_dirty)

    def test_blank_author_shows_validation_error_and_successful_retry_clears_it(self):
        dispatched = []
        def dispatch(callback, *args):
            dispatched.append(callback)
            return callback(*args)
        panel = self.list_panel(on_error=dispatch)
        field = next((w for w in Widget.widgets if w.kind == "StringField" and w.args[0].as_string == "Reviewer"), None)
        self.assertIsNotNone(field, "Author field must be available for validation")
        field.args[0].set_value("   ")
        self.click("Apply")
        self.assertEqual(len(dispatched), 1)
        self.assertEqual(self.service.author_name, "Reviewer")
        self.assertEqual(field.args[0].as_string, "   ")
        self.assertEqual(panel._error, "Enter an author name.")
        self.assertTrue(any(w.args and w.args[0] == "Enter an author name." and w.name == "error" for w in Widget.widgets))
        field.args[0].set_value("Corrected reviewer")
        self.click("Apply")
        self.assertEqual(self.service.author_name, "Corrected reviewer")
        self.assertEqual(panel._error, "")

    def test_author_refresh_tracks_current_setting_and_preserves_typed_name(self):
        panel = self.list_panel()
        field = next((w for w in Widget.widgets if w.kind == "StringField" and w.args[0].as_string == "Reviewer"), None)
        self.assertIsNotNone(field, "Author field must show the current setting")
        self.service.author_name = "Other reviewer"
        panel.refresh()
        self.assertEqual(field.args[0].as_string, "Other reviewer")
        field.args[0].set_value("Typing reviewer")
        self.service.author_name = "External reviewer"
        panel.refresh()
        self.assertEqual(field.args[0].as_string, "Typing reviewer")
        self.assertTrue(any(w.args and w.args[0] == "Current author: External reviewer" for w in Widget.widgets))

    def test_author_can_be_configured_without_scene_and_retained_apply_is_inert_after_destroy(self):
        self.service.stage = None
        panel = self.list_panel()
        field = next((w for w in Widget.widgets if w.kind == "StringField" and w.args[0].as_string == "Reviewer"), None)
        self.assertIsNotNone(field, "Attribution settings do not require an open scene")
        self.assertTrue(field.enabled)
        field.args[0].set_value("Ready reviewer")
        self.assertTrue(self.click("Apply").enabled)
        callback = next(w.clicked_fn for w in reversed(Widget.widgets) if w.args and w.args[0] == "Apply")
        self.assertEqual(self.service.author_name, "Ready reviewer")
        panel.destroy()
        field.args[0].set_value("Late reviewer")
        callback()
        self.assertEqual(self.service.author_name, "Ready reviewer")

    def test_placement_prompt_has_cancel_and_blocks_duplicate_create(self):
        panel = self.list_panel()
        self.assertTrue(hasattr(panel, "set_placement_state"), "Placement needs an explicit cancellation action")
        saved = tuple(self.service.records)
        panel.set_placement_state(True, on_cancel=lambda: self.events.append("cancel placement"))
        self.assertTrue(any(w.args and w.args[0] == "Click a model surface to place the issue pin." for w in Widget.widgets))
        self.assertFalse(self.click("Create issue").enabled)
        self.assertFalse(self.events)
        self.click("Cancel placement")
        self.assertEqual(self.events, ["cancel placement"])
        self.assertEqual(tuple(self.service.records), saved)
        panel.set_placement_state(False)
        self.assertTrue(self.click("Create issue").enabled)

    def test_destroyed_placement_cancel_callback_does_nothing(self):
        panel = self.list_panel()
        self.assertTrue(hasattr(panel, "set_placement_state"), "Placement needs an explicit cancellation action")
        panel.set_placement_state(True, on_cancel=lambda: self.events.append("late cancel"))
        callback = next(w.clicked_fn for w in reversed(Widget.widgets) if w.args and w.args[0] == "Cancel placement")
        panel.destroy()
        callback()
        panel.set_placement_state(False)
        self.assertFalse(self.events)


    def test_details_exposes_related_and_reattach_actions_without_direct_persistence(self):
        panel = self.details_panel()
        ref = SimpleNamespace(prim_path='/Wall', source_id='Wall')
        self.session.update(related_elements=(ref,))
        panel.refresh()
        for label in ('Add selected', 'Focus related', 'Reattach pin', 'Remove'):
            self.assertTrue(self.click(label).enabled)
        self.assertEqual(self.events, ['add related', 'focus related', 'reattach', ('remove related', ref)])
        self.assertEqual(self.session.record.related_elements, (ref,))
        panel.set_busy(True)
        for label in ('Add selected', 'Focus related', 'Reattach pin', 'Remove'):
            self.assertFalse(self.click(label).enabled)
        self.assertEqual(len(self.events), 4)

    def test_comment_composer_capture_annotation_add_and_existing_annotation_routes(self):
        panel = self.details_panel()
        panel.comment.set_value('Investigate second angle')
        self.click('Capture viewpoint')
        self.session.comment_viewpoint = SimpleNamespace(id='pending', snapshot=b'')
        comment = SimpleNamespace(id='comment', author='Reviewer', created_at='Today', text='Saved evidence', viewpoint_id='saved')
        self.session.update(comments=(comment,))
        panel.refresh()
        self.click('Annotate viewpoint')
        self.click('Annotate comment')
        self.click('Add comment')
        self.assertEqual(self.events, ['capture comment', ('annotate comment', None), ('annotate comment', 'comment'), 'add comment'])
        self.assertEqual(self.session.comment_text, 'Investigate second angle')
        panel.clear_comment()
        self.assertEqual(panel.comment.as_string, '')


    def test_main_and_comment_previews_use_provider_binding_aspect_fit_policy(self):
        panel = self.details_panel()
        ui = panel._snapshot.__globals__['ui']
        with self.assertRaisesRegex(TypeError, 'IwpFillPolicy'):
            ui.ImageWithProvider(object(), fill_policy=ui.FillPolicy.PRESERVE_ASPECT_FIT)
        panel._provider, panel._snapshot_bytes = object(), b'main'
        panel._comment_previews = {'saved': (object(), b'saved'), 'pending': (object(), b'pending')}
        panel._snapshot(SimpleNamespace(snapshot=b'main'))
        panel._comment_snapshot(SimpleNamespace(id='saved', snapshot=b'saved'))
        panel._comment_snapshot(SimpleNamespace(id='pending', snapshot=b'pending'))
        previews = [widget for widget in Widget.widgets if isinstance(widget, ImageWithProvider)]
        self.assertEqual(len(previews), 3)
        for preview in previews:
            self.assertIs(preview.fill_policy, IwpFillPolicy.IWP_PRESERVE_ASPECT_FIT)
            self.assertEqual(preview.height, 180)
        self.assertEqual(panel._snapshot_bytes, b'main')


if __name__ == "__main__":
    unittest.main()
