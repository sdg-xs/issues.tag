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

    def _file_picker_journey(self, *, change_scene):
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
                    preview.apply_choices()
                    self.assertEqual(len(sdk.service.list_issues()), 1)
                for dialog in sdk.extension._dialogs:
                    dialog.destroy()


if __name__ == '__main__':
    unittest.main()
