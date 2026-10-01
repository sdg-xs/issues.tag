"""Evidence keeps render/Markup content and restores controls on every exit."""
import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

from test_lifecycle import lifecycle_sdk

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('_evidence_capture_product', ROOT / 'issues_tag/evidence_capture.py')
product = importlib.util.module_from_spec(spec)
spec.loader.exec_module(product)


class Settings:
    def __init__(self):
        self.values = {}
    def get(self, key):
        return self.values.get(key)
    def set(self, key, value):
        self.values[key] = value
    def destroy_item(self, key):
        self.values.pop(key, None)


class EvidenceCaptureTests(unittest.TestCase):
    def exercise(self, failure=None):
        window = SimpleNamespace(dock_tab_bar_enabled=True)
        overlays = [SimpleNamespace(visible=True), SimpleNamespace(visible=False)]
        markup = SimpleNamespace(visible=True)
        floating = SimpleNamespace(visible=True)
        settings = Settings()
        def capture():
            with product.clean_evidence_ui(overlays, [floating], settings):
                self.assertFalse(floating.visible)
                self.assertFalse(any(layer.visible for layer in overlays))
                self.assertTrue(markup.visible)
                self.assertTrue(window.dock_tab_bar_enabled)
                if failure:
                    raise failure
        if failure:
            with self.assertRaises(type(failure)):
                capture()
        else:
            capture()
        self.assertEqual(settings.values, {})
        self.assertTrue(floating.visible)
        self.assertEqual([layer.visible for layer in overlays], [True, False])
        self.assertTrue(window.dock_tab_bar_enabled)

    def test_capture_hides_overlays_and_keeps_other_ui(self):
        self.exercise()

    def test_failed_capture_restores_controls(self):
        self.exercise(RuntimeError('capture failed'))

    def test_cancelled_capture_restores_controls(self):
        self.exercise(asyncio.CancelledError())

    def test_overlay_collection_excludes_render_and_other_viewports(self):
        with lifecycle_sdk() as sdk:
            render = SimpleNamespace(categories=('viewport',), visible=True)
            pins = SimpleNamespace(categories=('manipulator',), visible=True)
            menu = SimpleNamespace(categories=('menubar',), visible=True)
            stats = SimpleNamespace(categories=('stats',), visible=False)
            provider = SimpleNamespace(layers=[render, SimpleNamespace(layers=[pins]), menu, stats])
            api = object()
            adapter = sdk.viewport.ViewportAdapter(SimpleNamespace())
            adapter._items = [SimpleNamespace(viewport_api=object(), layer_provider=None),
                              SimpleNamespace(viewport_api=api, layer_provider=provider)]
            self.assertEqual(adapter.evidence_overlays(api), (pins, menu, stats))
            with product.clean_evidence_ui(adapter.evidence_overlays(api), [], Settings()):
                self.assertFalse(menu.visible)
                self.assertTrue(render.visible)
                self.assertFalse(pins.visible)
                self.assertFalse(stats.visible)
            self.assertTrue(render.visible)
            with self.assertRaises(ValueError):
                adapter.evidence_overlays(object())

    def test_only_overlapping_floating_windows_are_hidden(self):
        def window(title, x, y, visible=True, docked=False):
            return SimpleNamespace(title=title, visible=visible, docked=docked,
                position_x=x, position_y=y, width=100, height=100,
                frame=SimpleNamespace(screen_position_x=x, screen_position_y=y,
                                      computed_width=100, computed_height=100))
        viewport = window('Viewport', 100, 100)
        viewport.get_frame = lambda name: viewport.frame
        floating = window('Issue details', 120, 120)
        outside = window('Outside', 400, 400)
        docked = window('Stage', 100, 100, docked=True)
        hidden = window('Hidden', 120, 120, visible=False)
        windows = [viewport, floating, outside, docked, hidden]
        for handle in windows[1:]:
            del handle.frame
            self.assertFalse(hasattr(handle, "frame"))
        self.assertEqual(product.overlapping_windows(viewport, windows), (floating,))
        with product.clean_evidence_ui([], product.overlapping_windows(viewport, windows), Settings()):
            self.assertFalse(floating.visible)
            self.assertTrue(outside.visible)
            self.assertTrue(docked.visible)
            self.assertTrue(viewport.visible)
        self.assertTrue(floating.visible)
