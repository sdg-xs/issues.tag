"""Reference selection uses real dialog callbacks with native UI boundary doubles."""
import ast
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

from test_acc_ui import Combo, Widget, panel_types


def reference_window_type():
    path = Path(__file__).resolve().parents[1] / 'issues_tag/import_window.py'
    source = ast.parse(path.read_text(encoding='utf-8'), str(path))
    definitions = [node for node in source.body if isinstance(node, ast.ClassDef)]
    namespace = {'ui': panel_types()[0].__init__.__globals__['ui'], 'STYLE': {}}
    exec(compile(ast.Module(body=definitions, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace['ReferenceSelectionWindow']


class ImportReferenceTests(unittest.TestCase):
    def setUp(self):
        Widget.widgets.clear()

    def test_preview_requires_choice_and_passes_full_selected_path(self):
        selected = []
        paths = ('/World/Building/Default', '/World/Other/Default')
        panel = reference_window_type()(paths, selected.append)
        preview = next(w for w in Widget.widgets if w.kind == 'Button' and w.args == ('Preview import',))
        preview.clicked_fn()
        self.assertEqual(selected, [])
        self.assertEqual(panel.window.destroy_calls, 0)
        combo = next(w for w in Widget.widgets if isinstance(w, Combo))
        self.assertEqual(combo.args[2:], paths)
        combo.model.choose(2)
        preview.clicked_fn()
        self.assertEqual(selected, [paths[1]])
        self.assertEqual(panel.window.destroy_calls, 1)
        preview.clicked_fn()
        self.assertEqual(selected, [paths[1]])

    def test_cancel_does_not_preview_and_failed_preview_keeps_dialog(self):
        selected = []
        panel = reference_window_type()(('/World/SiteA', '/World/SiteB'), selected.append)
        cancel = next(w for w in Widget.widgets if w.kind == 'Button' and w.args == ('Cancel',))
        cancel.clicked_fn()
        self.assertEqual(selected, [])
        self.assertEqual(panel.window.destroy_calls, 1)
        def failed(path):
            raise ValueError('The scene changed. Import the file again.')
        panel = reference_window_type()(('/World/SiteA', '/World/SiteB'), failed)
        combo = [w for w in Widget.widgets if isinstance(w, Combo)][-1]
        combo.model.choose(1)
        preview = [w for w in Widget.widgets if w.kind == 'Button' and w.args == ('Preview import',)][-1]
        preview.clicked_fn()
        self.assertEqual(panel.window.destroy_calls, 0)
        self.assertIn('scene changed', panel._error)
        panel.destroy()

    def test_file_picker_opens_selector_then_preview_without_importing(self):
        self._file_picker_journey(change_scene=False)

    def test_scene_change_while_selecting_prevents_preview(self):
        self._file_picker_journey(change_scene=True)

    def test_replan_and_apply_use_current_plan_without_rereading_archive(self):
        self._file_picker_journey(change_scene=False, review_action='replan')

    def test_scene_change_blocks_all_review_callbacks(self):
        self._file_picker_journey(change_scene=False, review_action='scene')

    def test_shutdown_restores_preview_without_importing(self):
        self._file_picker_journey(change_scene=False, review_action='shutdown')

    def test_older_dialog_cannot_close_newer_dialog_preview(self):
        self._file_picker_journey(change_scene=False, review_action='ownership')

    def _file_picker_journey(self, *, change_scene, review_action=None):
        from test_acc_controller import controller_sdk
        from test_bcf_compat import BcfCompatibilityTests
        from pxr import Sdf, UsdGeom
        fixture = BcfCompatibilityTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.fixture()
        class Picker:
            def __init__(self, *args, **kwargs):
                self.apply = kwargs['click_apply_handler']
                self.hidden = False
            def show(self): pass
            def hide(self): self.hidden = True
            def destroy(self): pass
        with controller_sdk(self) as sdk:
            stage = sdk.service.stage
            for path in ('/World/SiteA', '/World/SiteB'):
                UsdGeom.Xform.Define(stage, path).GetPrim().CreateAttribute(
                    'omni:hoops:metadata:TYPE', Sdf.ValueTypeNames.String).Set('IFCSITE')
            ui = types.ModuleType('omni.ui')
            ui.__dict__.update(vars(panel_types()[0].__init__.__globals__['ui']))
            from test_import_camera_review import Provider
            ui.ByteImageProvider = Provider
            picker_module = types.ModuleType('omni.kit.window.filepicker')
            picker_module.FilePickerDialog = Picker
            package = sdk.service.__class__.__module__.rsplit('.', 1)[0]
            styles = types.ModuleType(package + '.styles')
            styles.STYLE = {}
            sdk.extension._window._call = lambda callback, *args: callback(*args)
            with patch.dict(sys.modules, {'omni.ui': ui, 'omni.kit.window.filepicker': picker_module,
                                         package + '.styles': styles}):
                sdk.extension.file_dialog(False)
                picker = sdk.extension._dialogs[0]
                picker.apply(fixture.path.name, str(fixture.path.parent))
                selector = sdk.extension._dialogs[1]
                self.assertTrue(picker.hidden)
                self.assertEqual(selector.paths, ('/World/SiteA', '/World/SiteB'))
                self.assertFalse(sdk.service.list_issues())
                if change_scene:
                    sdk.service.generation += 1
                selector._reference_model.choose(2)
                selector._select_clicked()
                if change_scene:
                    self.assertEqual(len(sdk.extension._dialogs), 2)
                    self.assertIn('scene changed', selector._error)
                    self.assertFalse(sdk.service.list_issues())
                else:
                    preview = sdk.extension._dialogs[2]
                    self.assertEqual(preview.plan.reference_path, '/World/SiteB')
                    self.assertFalse(sdk.service.list_issues())
                    if review_action:
                        self.assertTrue(callable(preview.on_replan), 'Controller replan callback is missing')
                        UsdGeom.Camera.Define(stage, '/BeforePreview')
                        sdk.viewport.viewport = types.SimpleNamespace(stage=stage, camera_path='/BeforePreview')
                        if review_action == 'scene':
                            preview._preview_clicked()
                            temporary = str(sdk.viewport.viewport.camera_path)
                            sdk.service.generation += 1
                            sdk.service._notify()
                            self.assertFalse(stage.GetPrimAtPath(temporary), 'Stale camera survives scene generation change')
                            for callback, argument in ((preview.on_replan, {}), (preview.on_preview, preview.plan.document.viewpoints[0]), (preview.on_apply, {})):
                                with self.assertRaisesRegex(ValueError, 'scene changed'):
                                    callback(argument)
                            self.assertFalse(sdk.service.list_issues())
                            preview.destroy()
                            return
                        preview._preview_clicked()
                        self.assertEqual(preview._error, '')
                        temporary = str(sdk.viewport.viewport.camera_path)
                        self.assertNotEqual(temporary, '/BeforePreview')
                        if review_action == 'shutdown':
                            sdk.extension.on_shutdown()
                            self.assertEqual(sdk.viewport.viewport.camera_path, '/BeforePreview')
                            self.assertFalse(stage.GetPrimAtPath(temporary))
                            return
                        if review_action == 'ownership':
                            sdk.extension.file_dialog(False)
                            sdk.extension._dialogs[-1].apply(fixture.path.name, str(fixture.path.parent))
                            selector2 = sdk.extension._dialogs[-1]
                            selector2._reference_model.choose(1)
                            selector2._select_clicked()
                            preview2 = sdk.extension._dialogs[-1]
                            preview2._preview_clicked()
                            newer = str(sdk.viewport.viewport.camera_path)
                            self.assertNotEqual(newer, temporary)
                            self.assertFalse(stage.GetPrimAtPath(temporary))
                            preview.destroy()
                            self.assertEqual(str(sdk.viewport.viewport.camera_path), newer)
                            preview2.cancel()
                            self.assertEqual(sdk.viewport.viewport.camera_path, '/BeforePreview')
                            self.assertFalse(stage.GetPrimAtPath(newer))
                            return
                        fixture.path.unlink()
                        preview._reference_model.choose(1)
                        preview._coordinate_model.choose(1)
                        preview._replan_clicked()
                        self.assertEqual(preview._error, '')
                        self.assertEqual(sdk.viewport.viewport.camera_path, '/BeforePreview')
                        self.assertEqual(preview.plan.document.viewpoints[0].coordinate_frame['bcf_reference_prim'], '/World/SiteA')
                    preview.apply_choices()
                    self.assertEqual(len(sdk.service.list_issues()), 1)
                    if review_action == 'replan':
                        stored = sdk.service.store.get_viewpoint(preview.plan.document.viewpoints[0].id)
                        self.assertEqual(stored.coordinate_frame['bcf_coordinate_mode'], 'reference_local')
                        self.assertEqual(stored.coordinate_frame['bcf_reference_prim'], '/World/SiteA')
                for dialog in sdk.extension._dialogs:
                    dialog.destroy()


if __name__ == '__main__':
    unittest.main()
