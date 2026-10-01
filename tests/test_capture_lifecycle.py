"""Offline ownership regression; framework events stand in for native render completion."""
import asyncio
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class CaptureLifecycleTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        omni = types.ModuleType('omni')
        omni.__path__ = []
        kit = types.ModuleType('omni.kit')
        kit.__path__ = []
        app = types.ModuleType('omni.kit.app')
        kit.app, omni.kit = app, kit
        pxr = types.ModuleType('pxr')
        pxr.Usd, pxr.UsdGeom = types.SimpleNamespace(), types.SimpleNamespace()
        self.modules = patch.dict(sys.modules, {'omni': omni, 'omni.kit': kit, 'omni.kit.app': app, 'pxr': pxr})
        self.modules.start()
        self.addCleanup(self.modules.stop)
        spec = importlib.util.spec_from_file_location('_capture_lifecycle_product', ROOT / 'issues_tag' / 'markup.py')
        self.product = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.product)
        self.adapter = self.product.MarkupAdapter(types.SimpleNamespace(stage=object(), generation=1))
        self.started = asyncio.Event()
        self.completed = asyncio.Event()
        self.cleanup = []
        async def native_capture():
            self.started.set()
            try:
                await self.completed.wait()
                return 'saved evidence'
            finally:
                self.cleanup.append('released')
        self.adapter._capture_viewpoint = native_capture

    async def test_caller_cancel_retains_capture_until_native_completion(self):
        caller = asyncio.create_task(self.adapter.capture_viewpoint())
        await self.started.wait()
        caller.cancel()
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        self.assertFalse(caller.done(), 'Cancellation released native capture before completion')
        self.assertEqual(self.cleanup, [])
        self.assertTrue(self.adapter._busy)
        with self.assertRaises(ValueError):
            await self.adapter.capture_viewpoint()
        self.completed.set()
        with self.assertRaises(asyncio.CancelledError):
            await caller
        self.assertEqual(self.cleanup, ['released'])
        self.assertFalse(self.adapter._busy)

    async def test_repeated_cancel_cannot_interrupt_native_drain(self):
        caller = asyncio.create_task(self.adapter.capture_viewpoint())
        await self.started.wait()
        for _ in range(3):
            caller.cancel()
            await asyncio.sleep(0)
            await asyncio.sleep(0)
        self.assertFalse(caller.done(), 'Repeated cancellation interrupted native drain')
        self.assertEqual(self.cleanup, [])
        self.completed.set()
        with self.assertRaises(asyncio.CancelledError):
            await caller

    async def test_destroy_does_not_allow_recapture_while_owned_work_is_pending(self):
        caller = asyncio.create_task(self.adapter.capture_viewpoint())
        await self.started.wait()
        caller.cancel()
        await asyncio.sleep(0)
        self.adapter.destroy()
        try:
            with self.assertRaises(Exception) as caught:
                await asyncio.wait_for(self.adapter.capture_viewpoint(), 0.05)
            self.assertIsInstance(caught.exception, ValueError, 'Destroy allowed overlapping native capture')
        finally:
            self.completed.set()
            try:
                await caller
            except asyncio.CancelledError:
                pass

    async def test_destroy_does_not_allow_annotation_while_capture_is_pending(self):
        caller = asyncio.create_task(self.adapter.capture_viewpoint())
        await self.started.wait()
        self.adapter.destroy()
        try:
            with self.assertRaises(Exception) as caught:
                await self.adapter.begin(types.SimpleNamespace())
            self.assertIsInstance(caught.exception, ValueError, 'Destroy allowed annotation during native capture')
        finally:
            self.completed.set()
            await caller

    async def test_creation_notification_waits_for_public_native_settling(self):
        await self._exercise_native_delivery()

    async def test_service_detach_retains_originating_capture_until_frame_delivery(self):
        await self._exercise_native_delivery(detach_service=True)

    async def _exercise_native_delivery(self, detach_service=False):
        from dataclasses import dataclass
        @dataclass
        class Record:
            markup_path: str = ''
            snapshot: bytes = b''
        notified = asyncio.Event()
        frame_started = asyncio.Event()
        delivered = asyncio.Event()
        events = []
        native = types.SimpleNamespace(path='/Viewport_Markups/Evidence', thumbnail_data=b'image')
        async def wait_native():
            events.append('native wait')
            await self.completed.wait()
        native.wait = wait_native
        callbacks = []
        core = types.SimpleNamespace(current_markup=None, editing_markup=None)
        def create(path):
            core.current_markup = core.editing_markup = native
            def notify():
                for callback in tuple(callbacks):
                    callback.on_markup_created(native)
                notified.set()
            asyncio.get_running_loop().call_soon(notify)
        def end(*args, **kwargs):
            events.append('ended')
            core.editing_markup = None
        core.create_markup, core.end_edit_markup = create, end
        core.get_markup = lambda name: native
        core.register_callback, core.deregister_callback = callbacks.append, callbacks.remove
        core.unlock_camera = lambda: events.append('unlocked')
        sdk = types.ModuleType('omni.kit.markup.core')
        sdk.MarkupChangeCallbacks = lambda **kwargs: types.SimpleNamespace(**kwargs)
        sys.modules['omni.kit.markup.core'] = sdk
        viewport_utility = types.ModuleType('omni.kit.viewport.utility')
        async def wait_frame(viewport, count):
            self.assertEqual(count, 2)
            events.append('frame wait')
            frame_started.set()
            await delivered.wait()
        viewport_utility.next_viewport_frame_async = wait_frame
        sys.modules['omni.kit.viewport.utility'] = viewport_utility
        stage = self.adapter.service.stage
        self.adapter.service._context = types.SimpleNamespace(get_stage=lambda: stage)
        self.adapter.service.store = types.SimpleNamespace(require_writable=lambda: None)
        self.adapter.core = core
        window = types.SimpleNamespace(viewport_api=types.SimpleNamespace(stage=stage))
        self.adapter._evidence_viewport = lambda: (window, types.SimpleNamespace(capture=lambda: Record()))
        async def ready():
            pass
        async def snapshot(*args):
            events.append('snapshot')
            return b'image'
        self.adapter._ready, self.adapter._snapshot = ready, snapshot
        del self.adapter._capture_viewpoint
        class Lease:
            def __init__(self, *args):
                events.append('lease held')
            def release(self):
                events.append('lease released')
        with patch.object(self.product, '_RootTargetLease', Lease):
            caller = asyncio.create_task(self.adapter.capture_viewpoint())
            await notified.wait()
            await asyncio.sleep(0)
            await asyncio.sleep(0)
            try:
                self.assertFalse(caller.done(), 'Creation callback prematurely completed native capture')
                self.assertNotIn('ended', events)
                self.assertNotIn('lease released', events)
                if detach_service:
                    caller.cancel()
                    await asyncio.sleep(0)
                    self.adapter.destroy()
                    self.adapter.service._context = None
                    self.adapter.service.stage = None
                self.completed.set()
                try:
                    await asyncio.wait_for(frame_started.wait(), 0.05)
                except TimeoutError:
                    pass
                self.assertTrue(frame_started.is_set(), 'Native settling released capture without viewport frame delivery')
                caller.cancel()
                await asyncio.sleep(0)
                self.adapter.destroy()
                self.assertFalse(caller.done(), 'Cancellation bypassed viewport delivery')
                self.assertNotIn('ended', events)
                self.assertNotIn('lease released', events)
            finally:
                self.completed.set()
                delivered.set()
                try:
                    await caller
                except asyncio.CancelledError:
                    pass
        self.assertLess(events.index('native wait'), events.index('ended'))
        self.assertLess(events.index('frame wait'), events.index('ended'))
        self.assertNotIn('snapshot', events)
        self.assertEqual(events[-1], 'lease released')


if __name__ == '__main__':
    unittest.main()
