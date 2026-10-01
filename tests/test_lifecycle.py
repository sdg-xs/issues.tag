"""Run real lifecycle code with narrow SDK boundaries and injected failures.

The temporary modules are restored before returning to the Kit dispatcher.
These cases prove Python cleanup/rollback ordering, not native scene disposal;
the lead must also run Kit runtime disable/re-enable and viewport cases.
"""
import importlib.util
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys

ROOT = Path(__file__).resolve().parents[1]


class Resource:
    def __init__(self, error=None):
        self.error = error
        self.calls = 0

    def destroy(self):
        self.calls += 1
        if self.error:
            raise RuntimeError(self.error)

    def Revoke(self):
        self.destroy()


@contextmanager
def lifecycle_sdk():
    saved = {}
    names = []
    resources = SimpleNamespace(registrations=[], services=[], markup_error=None, markup_start_error=None)

    def install(name, **values):
        saved[name] = sys.modules.get(name)
        module = ModuleType(name)
        module.__dict__.update(values)
        module.__path__ = []
        sys.modules[name] = module
        names.append(name)
        if '.' in name:
            parent, child = name.rsplit('.', 1)
            if parent in names:
                setattr(sys.modules[parent], child, module)
        return module

    class Registration(Resource):
        def __init__(self, factory, name):
            super().__init__()
            resources.registrations.append(self)

        def destroy(self):
            if self in resources.registrations:
                resources.registrations.remove(self)
            super().destroy()

    class Service(Resource):
        def __init__(self):
            super().__init__()
            self.stage = None
            self.viewport = None
            resources.services.append(self)

    class Markup(Resource):
        def restore_viewpoint(self, record):
            return False

        def __init__(self, service):
            if resources.markup_start_error:
                raise RuntimeError(resources.markup_start_error)
            super().__init__(resources.markup_error)

    try:
        install('omni')
        install('omni.ext', IExt=type('IExt', (), {}))
        install('omni.ui')
        install('omni.kit')
        install('omni.kit.app', get_app=lambda: SimpleNamespace(get_update_event_stream=lambda: SimpleNamespace(create_subscription_to_pop=lambda *a, **kw: Resource())))
        install('omni.kit.menu')
        install('omni.kit.menu.utils', MenuItemDescription=lambda **kw: SimpleNamespace(**kw), add_menu_items=lambda *a: None, remove_menu_items=lambda *a: None)
        install('omni.kit.viewport')
        install('omni.kit.viewport.utility')
        install('omni.kit.viewport.registry', RegisterScene=Registration)
        install('pxr', **{name: SimpleNamespace() for name in ('Gf', 'Sdf', 'Tf', 'Usd', 'UsdGeom')})
        install('_issues_lifecycle', __path__=[str(ROOT / 'issues_tag')])
        install('_issues_lifecycle.service', IssueService=Service)
        install('_issues_lifecycle.markup', MarkupAdapter=Markup)
        install('_issues_lifecycle.toolbar', IssuesToolbarButton=lambda on_open: Resource())
        install('_issues_lifecycle.elements', **{name: lambda *a: None for name in ('make_anchor', 'reference_for_prim', 'resolve_element', 'world_anchor')})
        install('_issues_lifecycle.model', Status=SimpleNamespace(OPEN='Open', IN_PROGRESS='In progress', RESOLVED='Resolved', CLOSED='Closed'), ViewpointRecord=SimpleNamespace)
        for name in ('viewport', 'extension'):
            full_name = '_issues_lifecycle.' + name
            saved[full_name] = sys.modules.get(full_name)
            names.append(full_name)
            spec = importlib.util.spec_from_file_location(full_name, ROOT / 'issues_tag' / (name + '.py'))
            module = importlib.util.module_from_spec(spec)
            sys.modules[full_name] = module
            spec.loader.exec_module(module)
            setattr(resources, name, module)
        yield resources
    finally:
        for name in reversed(names):
            if saved[name] is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = saved[name]


def _failure(operation):
    try:
        operation()
    except Exception as error:
        return error
    raise AssertionError('The original lifecycle failure must remain visible')


def test_shutdown_cleans_viewport_when_markup_teardown_fails():
    with lifecycle_sdk() as sdk:
        sdk.markup_error = 'markup teardown failed'
        extension = sdk.extension.IssuesExtension()
        extension.on_startup('issues.tag')
        service = extension._controller._service
        viewport = service.viewport
        error = _failure(extension.on_shutdown)
        assert 'markup teardown failed' in str(error) or 'markup teardown failed' in repr(error)
        assert not sdk.registrations, 'Markup teardown failure left a viewport factory registered'
        assert service.calls == 1, 'Service cleanup was skipped'
        assert viewport._registration is None
        assert sdk.extension.get_runtime_service() is None
        extension.on_shutdown()


def test_viewport_cleanup_continues_after_notice_and_item_failures():
    with lifecycle_sdk() as sdk:
        adapter = sdk.viewport.ViewportAdapter(sdk.services[0] if sdk.services else SimpleNamespace(stage=None))
        adapter.start()
        notice = Resource('notice revoke failed')
        first = Resource('scene item failed')
        last = Resource()
        adapter._scene_notice = notice
        adapter._items = [first, last]
        _failure(adapter.destroy)
        assert not sdk.registrations, 'Notice revoke failure left a viewport factory registered'
        assert first.calls == last.calls == notice.calls == 1, 'Cleanup stopped before all resources were attempted'
        assert adapter._registration is None and adapter._scene_notice is None and not adapter._items
        adapter.destroy()


def test_partial_extension_startup_unregisters_viewport():
    with lifecycle_sdk() as sdk:
        sdk.markup_start_error = 'markup startup failed'
        extension = sdk.extension.IssuesExtension()
        _failure(lambda: extension.on_startup('issues.tag'))
        assert not sdk.registrations, 'A failed startup left a viewport factory registered'
        assert sdk.services[0].calls == 1
        assert sdk.extension.get_runtime_service() is None
        extension.on_shutdown()


def test_partial_viewport_startup_unregisters_factory():
    with lifecycle_sdk() as sdk:
        adapter = sdk.viewport.ViewportAdapter(SimpleNamespace(stage=None))
        def fail_notice(stage):
            raise RuntimeError('notice registration failed')
        adapter._bind_scene = fail_notice
        _failure(adapter.start)
        assert not sdk.registrations, 'A failed scene subscription left its viewport factory registered'
        assert adapter._registration is None and adapter._update_sub is None
        adapter.destroy()





def test_registry_callbacks_can_reenter_scene_item_cleanup():
    with lifecycle_sdk() as sdk:
        adapter = sdk.viewport.ViewportAdapter(SimpleNamespace(stage=None))
        adapter.start()
        item = sdk.viewport._ViewportItem.__new__(sdk.viewport._ViewportItem)
        item.adapter = adapter
        item.pins = ()
        item.visible_issue_ids = ('old issue',)
        manipulator = Resource('manipulator destroy failed')
        item.manipulator = manipulator
        adapter._items.append(item)
        registration = adapter._registration
        unregister = registration.destroy
        def unload():
            unregister()
            item.destroy()
        registration.destroy = unload
        _failure(adapter.destroy)
        assert not sdk.registrations and not adapter._items
        assert manipulator.calls == 1, 'Registry reentry destroyed the same manipulator twice'
        assert item.manipulator is None and not item.visible_issue_ids
        adapter.destroy()


def test_cleanup_restores_sdk_modules_after_stubbed_load():
    before = {name: sys.modules.get(name) for name in ('omni', 'omni.kit.app', 'pxr')}
    with lifecycle_sdk():
        assert sys.modules['omni'] is not before['omni']
    assert all(sys.modules.get(name) is original for name, original in before.items())


def test_context_restore_can_leave_native_markup_camera_untouched():
    from contextlib import nullcontext
    with lifecycle_sdk() as sdk:
        stage = SimpleNamespace(GetSessionLayer=lambda: None, GetPrimAtPath=lambda path: None)
        selected = []
        selection = SimpleNamespace(set_selected_prim_paths=lambda paths, expand: selected.append(paths))
        service = SimpleNamespace(stage=stage, _context=SimpleNamespace(get_selection=lambda: selection))
        viewport = SimpleNamespace(stage=stage, camera_path='/NativeMarkupCamera', render_product_path='/RenderProduct')
        adapter = sdk.viewport.ViewportAdapter(service, viewport)
        sdk.viewport.Usd.EditContext = lambda *args: nullcontext()
        def unexpected_camera(*args):
            raise AssertionError('Context-only restoration must not author a camera')
        sdk.viewport.UsdGeom.Camera = unexpected_camera
        record = SimpleNamespace(coordinate_frame={}, camera=dict(projection='perspective', transform=[0] * 16,
                                 horizontal_aperture=20, vertical_aperture=15, focal_length=35, clipping_range=[.1, 100]),
                                 section_state={}, visibility=(), selection=(), clipping_planes=())
        adapter.restore(record, restore_camera=False)
        assert viewport.camera_path == '/NativeMarkupCamera'
        assert selected == [[]], 'Context-only restore must still apply saved selection'


def test_viewport_startup_without_render_product_has_no_clipping_planes():
    with lifecycle_sdk() as sdk:
        def unexpected_lookup(path):
            raise AssertionError('An uninitialized render product must not query USD')
        viewport = SimpleNamespace(stage=SimpleNamespace(GetPrimAtPath=unexpected_lookup), render_product_path=None)
        adapter = sdk.viewport.ViewportAdapter(SimpleNamespace(), viewport)
        assert adapter.clipping_planes() == ()


import asyncio
import gc
import unittest
import weakref


class ManagerShutdownTests(unittest.IsolatedAsyncioTestCase):
    async def test_manager_clear_keeps_pending_controller_until_capture_drains(self):
        with lifecycle_sdk() as sdk:
            extension = sdk.extension.IssuesExtension()
            extension.on_startup('issues.tag')
            controller = extension._controller
            service, markup = controller._service, controller._markup
            started, delivery = asyncio.Event(), asyncio.Event()
            events, loop_errors = [], []
            loop = asyncio.get_running_loop()
            prior_handler = loop.get_exception_handler()
            loop.set_exception_handler(lambda loop, context: loop_errors.append(context))
            async def native_capture():
                started.set()
                try:
                    await asyncio.Future()
                except asyncio.CancelledError:
                    await delivery.wait()
                    events.append('native drained')
                    raise
            controller._dispatch(lambda: controller._operation(native_capture))
            await started.wait()
            extension.on_shutdown()
            shutdown = controller._shutdown_task
            # Exact manager behavior: on_shutdown returns, then manager clears IExt state.
            wrapper_ref = weakref.ref(extension)
            extension.__dict__.clear()
            extension = None
            gc.collect()
            self.assertIsNone(wrapper_ref(), 'Pending work retained the manager-owned IExt wrapper')
            fresh = sdk.extension.IssuesExtension()
            try:
                await asyncio.sleep(0)
                self.assertEqual(service.calls, 0)
                self.assertEqual(markup.calls, 0)
                self.assertFalse(shutdown.done())
                fresh.on_startup('issues.tag')
                new_controller = fresh._controller
                new_service = new_controller._service
                self.assertIsNot(controller, new_controller)
                delivery.set()
                await shutdown
                await asyncio.sleep(0)
                self.assertEqual(events, ['native drained'])
                self.assertEqual(service.calls, 1)
                self.assertEqual(markup.calls, 1)
                self.assertEqual(new_service.calls, 0)
                self.assertIs(sdk.extension.get_runtime_service(), new_service)
                self.assertEqual(loop_errors, [])
                self.assertEqual(len(sdk.registrations), 1)
            finally:
                delivery.set()
                if not shutdown.done():
                    await shutdown
                fresh.on_shutdown()
                fresh.__dict__.clear()
                loop.set_exception_handler(prior_handler)
            self.assertFalse(sdk.registrations)
            self.assertIsNone(sdk.extension.get_runtime_service())


if __name__ == '__main__':
    failures = []
    for name, operation in tuple(globals().items()):
        if name.startswith('test_'):
            try:
                operation()
                print('PASS:', name)
            except Exception as error:
                failures.append(name)
                print('FAIL:', name, repr(error))
    raise SystemExit(bool(failures))
