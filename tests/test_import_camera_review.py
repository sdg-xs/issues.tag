"""Real review callbacks with offline omni.ui doubles, not rendered acceptance."""
import ast
import importlib
from io import BytesIO
from pathlib import Path
from dataclasses import replace
from types import SimpleNamespace
import unittest

from test_acc_ui import Combo, Widget, panel_types
import test_bcf_camera_options as camera_tests


class Provider:
    def set_bytes_data(self, pixels, size):
        self.pixels, self.size = pixels, size


def review_type():
    camera_tests.CameraOptionsTests.setUpClass()
    path = Path(__file__).resolve().parents[1] / 'issues_tag/import_window.py'
    definitions = [node for node in ast.parse(path.read_text(encoding='utf-8')).body if isinstance(node, (ast.ClassDef, ast.FunctionDef))]
    ui = panel_types()[0].__init__.__globals__['ui']
    ui.ByteImageProvider = Provider
    namespace = {'ui': ui, 'STYLE': {}, 'BytesIO': BytesIO,
                 'camera_diagnostics': importlib.import_module('_bcf_compat_product.bcf_diagnostics').camera_diagnostics,
                 'ViewpointImportOptions': importlib.import_module('_bcf_compat_product.bcf_coordinates').ViewpointImportOptions}
    exec(compile(ast.Module(body=definitions, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace['ImportWindow']


class ImportCameraReviewTests(unittest.TestCase):
    def setUp(self):
        self.window_type = review_type()
        self.fixture = camera_tests.CameraOptionsTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.stage = self.fixture.stage().stage
        self.store = self.fixture.store_api.IssueStore(self.stage)
        self.source = self.fixture.document()
        self.plan = self.fixture.api.plan_import(self.source, self.store, reference_path='/World/A/Site')
        self.closed, self.previews, self.applies, self.replans = [], [], [], []
        Widget.widgets.clear()

    def panel(self, **extra):
        self.assertIn('on_replan', __import__('inspect').signature(self.window_type).parameters,
                      'Camera review callbacks are missing')
        def replan(options):
            self.replans.append(options)
            return self.fixture.api.plan_import(self.source, self.store, reference_path='/World/A/Site', viewpoint_options=options)
        panel = self.window_type(self.plan, self.applies.append, on_replan=replan,
            on_preview=self.previews.append, on_close_preview=lambda: self.closed.append(True),
            reference_paths=('/World/A/Site', '/World/B/Site'), **extra)
        self.addCleanup(panel.destroy)
        return panel

    def combo(self, label):
        return next(w for w in reversed(Widget.widgets) if isinstance(w, Combo) and label in w.args)

    def click(self, label):
        next(w for w in reversed(Widget.widgets) if w.kind == 'Button' and w.args == (label,)).clicked_fn()

    def test_controls_replan_source_preserve_conflicts_and_preview_converted_camera(self):
        conflict = SimpleNamespace(key='topic.description', field='description', topic_id='topic', local='Local', incoming='BCF')
        self.plan = replace(self.plan, conflicts=(conflict,))
        panel = self.panel()
        panel.set_choice(conflict.key, 'use_imported')
        original_replan = panel.on_replan
        panel.on_replan = lambda options: replace(original_replan(options), conflicts=(conflict,))
        self.combo('Source world').model.choose(1)
        self.combo('File interpretation').model.choose(1)
        self.click('Recalculate camera')
        selected = panel.plan.document.viewpoints[0]
        self.assertEqual(selected.coordinate_frame['bcf_coordinate_mode'], 'reference_local')
        self.assertEqual(selected.coordinate_frame['bcf_fov_mode'], 'horizontal')
        self.assertEqual(panel.plan.source_document.viewpoints[0].camera, self.source.viewpoints[0].camera)
        self.assertEqual(panel.plan.source_document.viewpoints[0].snapshot, self.source.viewpoints[0].snapshot)
        self.assertEqual(panel.choices[conflict.key], 'use_imported')
        self.click('Preview camera')
        self.assertEqual(self.previews, [selected])
        self.click('Apply import')
        self.assertEqual(self.applies, [{conflict.key: 'use_imported'}])
        self.assertTrue(panel.applied)
        self.assertTrue(self.closed)
        self.assertFalse(next(w for w in reversed(Widget.widgets) if w.kind == 'Button' and w.args == ('Recalculate camera',)).enabled)
        self.assertFalse(self.store.list_issues())

    def test_failed_replan_and_preview_keep_valid_plan_and_show_error(self):
        panel = self.panel()
        panel.on_replan = lambda options: (_ for _ in ()).throw(ValueError('Unresolved reference'))
        self.combo('Source world').model.choose(1)
        self.click('Recalculate camera')
        self.assertIs(panel.plan, self.plan)
        self.assertIn('Unresolved reference', panel._error)
        self.assertEqual(self.combo('Source world').model.get_item_value_model().as_int, 1)
        panel.select_viewpoint(panel.selected_viewpoint_id)
        panel.on_preview = lambda view: (_ for _ in ()).throw(ValueError('No active viewport'))
        self.click('Preview camera')
        self.assertIn('No active viewport', panel._error)
        self.assertFalse(self.store.list_issues())

    def test_camera_less_evidence_is_selectable_and_native_close_cleans_preview(self):
        extra = replace(self.source.viewpoints[0], id='22222222-2222-4222-8222-222222222222', camera={})
        source = replace(self.source, viewpoints=(*self.source.viewpoints, extra),
                         viewpoint_topics=(*self.source.viewpoint_topics, (extra.id, self.source.issues[0].id)))
        self.plan = self.fixture.api.plan_import(source, self.store, reference_path='/World/A/Site')
        panel = self.panel()
        panel.select_viewpoint(extra.id)
        self.assertEqual(panel.selected_viewpoint_id, extra.id)
        self.assertTrue(any(w.kind == 'ImageWithProvider' for w in Widget.widgets))
        self.assertFalse(next(w for w in reversed(Widget.widgets) if w.kind == 'Button' and w.args == ('Preview camera',)).enabled)
        panel.window.visibility_callback(False)
        self.assertTrue(panel._destroyed)
        self.assertTrue(self.closed)
        self.assertFalse(self.applies)

    def test_cancel_closes_preview_and_late_callbacks_are_blocked(self):
        panel = self.panel()
        apply = next(w for w in reversed(Widget.widgets) if w.kind == 'Button' and w.args == ('Apply import',))
        self.click('Cancel')
        apply.clicked_fn()
        self.assertFalse(self.applies)
        self.assertTrue(self.closed)

    def test_unrecalculated_options_cannot_preview_or_apply_the_old_camera(self):
        panel = self.panel()
        self.combo('Source world').model.choose(1)
        self.click('Preview camera')
        self.assertFalse(self.previews, 'Pending corrections must not preview the old camera')
        self.click('Apply import')
        self.assertFalse(self.applies)
        self.assertIn('Recalculate', panel._error)

    def test_orthographic_and_native_camera_correction_controls_are_limited(self):
        for native in (False, True):
            source = replace(self.source, native_viewpoints=(self.source.viewpoints[0].id,)) if native else self.fixture.document(perspective=False)
            self.plan = self.fixture.api.plan_import(source, self.store, reference_path='/World/A/Site')
            panel = self.panel()
            self.assertFalse(self.combo('File interpretation').enabled)
            self.assertEqual(self.combo('Source world').enabled, not native)
            panel.destroy()

    def test_viewpoint_selector_keeps_corrections_independent(self):
        first = self.source.viewpoints[0]
        second = replace(first, id='33333333-3333-4333-8333-333333333333')
        self.source = replace(self.source, viewpoints=(first, second),
            viewpoint_topics=(*self.source.viewpoint_topics, (second.id, self.source.issues[0].id)))
        self.plan = self.fixture.api.plan_import(self.source, self.store, reference_path='/World/A/Site')
        panel = self.panel()
        self.combo('Source world').model.choose(1)
        self.click('Recalculate camera')
        selector = next(w for w in reversed(Widget.widgets) if isinstance(w, Combo) and any(second.id in str(arg) for arg in w.args))
        selector.model.choose(1)
        self.assertEqual(panel.selected_viewpoint_id, second.id)
        self.combo('Import reference / scene').model.choose(2)
        self.click('Recalculate camera')
        options = dict(panel.plan.viewpoint_options_signatures)
        self.assertEqual(options[first.id].coordinate_mode, 'reference_local')
        self.assertEqual(options[first.id].reference_path, '/World/A/Site')
        self.assertEqual(options[second.id].coordinate_mode, 'source_world')
        self.assertEqual(options[second.id].reference_path, '/World/B/Site')


if __name__ == '__main__':
    unittest.main()
