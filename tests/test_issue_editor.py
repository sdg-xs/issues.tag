"""Offline native-editor behavior checks without importing or replacing Kit modules."""

import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
import unittest


class Widget:
    def __init__(self, *args, **kwargs):
        self.__dict__.update(kwargs)
        self.visible = True
        self.frame = self
        self.visibility_callback = None
        self.destroy_calls = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def set_build_fn(self, callback):
        self.build = callback

    def rebuild(self):
        self.build()

    def set_visibility_changed_fn(self, callback):
        self.visibility_callback = callback

    def destroy(self):
        assert self.visibility_callback is None, "Detach visibility callback before destroying the native window"
        self.destroy_calls += 1


class StringModel:
    def __init__(self, value):
        self.as_string = value

    def set_value(self, value):
        self.as_string = value


def editor_type():
    path = Path(__file__).resolve().parent.parent / "issues_tag" / "issue_editor.py"
    assert path.exists(), "Issue creation editor is not implemented"
    source = ast.parse(path.read_text(encoding="utf-8"), str(path))
    definition = next(node for node in source.body if isinstance(node, ast.ClassDef) and node.name == "DirtyDetailsDialog")
    ui = SimpleNamespace(Window=Widget, VStack=Widget, HStack=Widget, ScrollingFrame=Widget,
                         Label=Widget, StringField=Widget, Button=Widget, Separator=Widget,
                         SimpleStringModel=StringModel)
    namespace = {"asyncio": asyncio, "ui": ui, "STYLE": {}}
    exec(compile(ast.Module(body=[definition], type_ignores=[]), str(path), "exec"), namespace)
    return namespace["DirtyDetailsDialog"]


class IssueEditorTests(unittest.IsolatedAsyncioTestCase):
    async def test_explicit_decision_waits_for_controller_cleanup(self):
        for decision in ('save', 'discard', 'stay'):
            editor = editor_type()()
            try:
                editor.choose(decision)
                self.assertEqual(await editor.wait(), decision)
                self.assertEqual(editor.window.destroy_calls, 0)
                editor.choose('stay')
                self.assertEqual(await editor.wait(), decision)
            finally:
                editor.destroy()

    async def test_native_close_means_stay(self):
        editor = editor_type()()
        try:
            editor.window.visibility_callback(False)
            self.assertEqual(await editor.wait(), 'stay')
        finally:
            editor.destroy()

    async def test_destroy_resolves_wait_and_detaches_native_callback_once(self):
        editor = editor_type()()
        window = editor.window
        editor.destroy()
        self.assertEqual(await editor.wait(), 'stay')
        self.assertIsNone(window.visibility_callback)
        self.assertEqual(window.destroy_calls, 1)
        editor.destroy()
        editor.choose('save')
        self.assertEqual(window.destroy_calls, 1)
