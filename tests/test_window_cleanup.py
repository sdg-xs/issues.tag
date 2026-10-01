"""Standalone destructor checks using SDK boundary stubs, without Kit imports."""

import ast
import asyncio
import inspect
from pathlib import Path
import unittest


def window_type():
    path = Path(__file__).resolve().parent.parent / "issues_tag" / "window.py"
    source = ast.parse(path.read_text(encoding="utf-8"), str(path))
    definition = next(node for node in source.body if isinstance(node, ast.ClassDef) and node.name == "IssuesWindow")
    namespace = {"asyncio": asyncio, "inspect": inspect}
    exec(compile(ast.Module(body=[definition], type_ignores=[]), str(path), "exec"), namespace)
    return namespace["IssuesWindow"]


class Resource:
    def __init__(self, name, attempts, fail=False):
        self.name, self.attempts, self.fail = name, attempts, fail

    def destroy(self):
        self.attempts.append(self.name)
        if self.fail:
            raise RuntimeError(self.name)

    cancel = destroy


class Service:
    def __init__(self, attempts, fail=False):
        self.attempts, self.fail = attempts, fail

    def remove_listener(self, callback):
        self.attempts.append("listener")
        if self.fail:
            raise RuntimeError("listener")


def make_window(attempts, *, fail_listener=False, fail_main=False):
    from types import SimpleNamespace
    kind = window_type()
    window = kind.__new__(kind)
    window._destroyed = False
    window.service = Service(attempts, fail_listener)
    window.service.viewport = SimpleNamespace(filtered_issue_ids=frozenset({'old'}))
    window.search = SimpleNamespace(remove_value_changed_fn=lambda listener: attempts.append('search listener'))
    window._search_listener = object()
    window.window = Resource('main', attempts, fail_main)
    return window


def leaf_errors(error):
    if isinstance(error, BaseExceptionGroup):
        return [message for child in error.exceptions for message in leaf_errors(child)]
    return [str(error)]


class WindowCleanupTests(unittest.TestCase):
    def test_destroy_attempts_all_resources_and_aggregates_failures(self):
        attempts = []
        window = make_window(attempts, fail_listener=True, fail_main=True)
        viewport = window.service.viewport
        with self.assertRaises(ExceptionGroup) as raised:
            window.destroy()
        self.assertEqual(set(attempts), {'listener', 'search listener', 'main'})
        self.assertEqual(set(leaf_errors(raised.exception)), {'listener', 'main'})
        self.assertIsNone(window.service)
        self.assertIsNone(window.window)
        self.assertIsNone(viewport.filtered_issue_ids)
        before = list(attempts)
        window.destroy()
        self.assertEqual(attempts, before)

    def test_late_native_callbacks_do_nothing_after_destruction(self):
        attempts = []
        window = make_window(attempts)
        window.destroy()
        before = list(attempts)
        window._call(lambda: attempts.append('late action'))
        window.select_issue('old issue')
        window._create()
        self.assertEqual(attempts, before)
