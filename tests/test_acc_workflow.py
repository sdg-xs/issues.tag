"""Rendered ACC acceptance. Only the lead launches this through verify_kit.py."""
import asyncio
import io
import json
import sys
from datetime import datetime, timezone
from unittest.mock import patch

from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux
from verify_kit import APP, ROOT, enable_extension, frames

def _read_property(obj, name):
    try:
        return getattr(obj, name, None)
    except Exception as error:
        return f'{type(error).__name__}: {error}'


def _geometry(widget):
    if widget is None:
        return None
    result = {}
    for name in ('visible', 'docked', 'screen_position_x', 'screen_position_y', 'computed_width', 'computed_height'):
        try:
            value = getattr(widget, name, None)
            result[name] = value if isinstance(value, (bool, int, float, str, type(None))) else str(value)
        except Exception as error:
            result[name] = str(error)
    return result


def _window_state(handle, frame=None, point=None):
    # Workspace supplies WindowHandle, which has no frame. Only caller-owned
    # native windows supply frame geometry; external handles expose window props.
    bounds = _geometry(frame)
    contains = None
    rectangle = ('screen_position_x', 'screen_position_y', 'computed_width', 'computed_height')
    if point and bounds and all(isinstance(bounds[key], (int, float)) for key in rectangle):
        x, y = bounds['screen_position_x'], bounds['screen_position_y']
        contains = x <= point[0] <= x + bounds['computed_width'] and y <= point[1] <= y + bounds['computed_height']
    return {'title': _read_property(handle, 'title'), 'visible': _read_property(handle, 'visible'),
            'docked': _read_property(handle, 'docked'), 'position_x': _read_property(handle, 'position_x'),
            'position_y': _read_property(handle, 'position_y'), 'width': _read_property(handle, 'width'),
            'height': _read_property(handle, 'height'), 'dock_id': _read_property(handle, 'dock_id'),
            'frame': bounds, 'contains_click': contains}


def _task_state(task):
    if task is None:
        return None
    chain, awaitable = [], task.get_coro()
    for _ in range(20):
        frame = getattr(awaitable, 'cr_frame', None) or getattr(awaitable, 'gi_frame', None)
        if frame:
            chain.append(f'{frame.f_code.co_filename}:{frame.f_lineno}:{frame.f_code.co_name}')
        awaitable = getattr(awaitable, 'cr_await', None) or getattr(awaitable, 'gi_yieldfrom', None)
        if awaitable is None:
            break
    return {'name': task.get_name(), 'done': task.done(), 'cancelled': task.cancelled(), 'await_chain': chain}


def _trace(phase, extension=None, service=None, point=None):
    """Read-only diagnostics. A diagnostic failure must not replace the test failure."""
    try:
        import omni.ui as ui
        import carb.settings
        from omni.kit.viewport.utility import get_active_viewport_window
        service = service or extension._service
        adapter = service.viewport
        window = get_active_viewport_window('Viewport')
        viewport = window.viewport_api
        mainwindow_module = sys.modules.get('omni.kit.mainwindow')
        known_windows = {window.title: window}
        if extension:
            for panel in (extension._window, extension._details):
                if panel and panel.window:
                    known_windows[panel.window.title] = panel.window
        windows = []
        for other in ui.Workspace.get_windows():
            owned = known_windows.get(_read_property(other, 'title'))
            windows.append(_window_state(other, owned.frame if owned else None, point))
        tool_module = sys.modules.get('omni.kit.tool.markup')
        tool = tool_module.get_instance() if tool_module else None
        core_module = sys.modules.get('omni.kit.markup.core')
        core = core_module.get_instance() if core_module else None
        session = extension._session if extension else None
        tasks = set(extension._tasks) if extension else set()
        if extension and extension._edit_task:
            tasks.add(extension._edit_task)
        capture_task = getattr(getattr(extension, '_markup', None), '_capture_task', None)
        if capture_task:
            tasks.add(capture_task)
        progress = ROOT / 'verification' / 'progress.json'
        test_name = json.loads(progress.read_text(encoding='utf-8')).get('current_test') if progress.exists() else None
        state = {
            'at': datetime.now(timezone.utc).isoformat(), 'test': test_name, 'phase': phase, 'click': point,
            'viewport': {'frame': _geometry(window.frame), 'widget': _geometry(window.viewport_widget),
                         'visible': window.visible, 'docked': window.docked, 'camera': str(viewport.camera_path),
                         'flags': str(_read_property(window, 'flags')),
                         'lock_to_render_result': viewport.lock_to_render_result, 'updates_enabled': viewport.updates_enabled,
                         'matches_service_stage': viewport.stage == service.stage,
                         'matches_adapter': viewport == adapter.viewport,
                         'matches_placement': viewport == adapter._placement_viewport},
            'layout': {'main_window_registered': bool(mainwindow_module and mainwindow_module.get_main_window()),
                       'dockspace': _window_state(ui.Workspace.get_window('DockSpace')),
                       'viewport_dock_id': _read_property(window, 'dock_id'),
                       'workspace_viewport_is_instance': ui.Workspace.get_window(window.title) is window,
                       'mainwindow_extension_enabled': APP.get_extension_manager().is_extension_enabled('omni.kit.mainwindow'),
                       'settings': {path: carb.settings.get_settings().get(path) for path in (
                           '/exts/omni.kit.viewport.window/startup/dockTabInvisible', '/app/renderer/skipWhileInvisible')}},
            'placement': {'active': adapter.is_placing, 'list_prompt': extension._window._placing if extension else None,
                          'items': [{'same_viewport': item.viewport_api == viewport,
                                     'objects': len(getattr(item.manipulator, '_objects', ())),
                                     'layer_provider': type(item.layer_provider).__name__,
                                     'signature_armed': bool(item._signature and item._signature[-1])}
                                    for item in adapter._items]},
            'session': {'id': session.record.id, 'is_new': session.is_new,
                        'viewpoint': session.viewpoint.id if session.viewpoint else None} if session else None,
            'markup': {'current': str(getattr(core, 'current_markup', None)),
                       'editing': str(getattr(core, 'editing_markup', None)),
                       'canvas': _geometry(getattr(tool, '_canvas', None)),
                       'scene_view': _geometry(getattr(tool, '_scene_view', None)),
                       'tool_frame': _geometry(getattr(tool, '_tool_frame', None))},
            'owned_tasks': [_task_state(task) for task in tasks], 'windows': windows,
            'ui_errors': {'list': getattr(getattr(extension, '_window', None), '_error', None),
                          'details': getattr(getattr(extension, '_details', None), '_error', None)},
        }
        with (ROOT / 'verification' / 'acc-workflow-diagnostics.jsonl').open('a', encoding='utf-8') as output:
            output.write(json.dumps(state) + '\n')
        print('ISSUES_ACC_PHASE', phase, json.dumps({'placing': adapter.is_placing, 'session': state['session'],
              'canvas': state['markup']['canvas'], 'click': point}), flush=True)
    except Exception as error:
        print('ISSUES_ACC_DIAGNOSTIC_ERROR', phase, repr(error), flush=True)


async def _native_dependencies():
    # The actual capture adapter activates Markup Tool after pin placement.
    # Eager startup creates its input-owning canvas before any active-Markup event.
    for name in ('omni.kit.ui_test', 'omni.kit.markup.core'):
        assert enable_extension(name), f'Private dependency cannot activate: {name}'
    await frames(10)


async def _dock_primary_viewport(service):
    import omni.ui as ui
    from omni.kit.mainwindow import get_main_window
    from omni.kit.viewport.utility import get_active_viewport_window, next_viewport_frame_async
    # Match the SDK viewport layout tests: MainWindow is an app dependency,
    # so its owner and startup docking exist before the Viewport is created.
    assert get_main_window() is not None, 'Native MainWindow extension has no owner'
    await frames(10)
    window = get_active_viewport_window('Viewport')
    _trace('native_mainwindow_startup_layout', service=service)
    assert ui.Workspace.get_window('DockSpace') is not None, 'Native MainWindow did not create DockSpace'
    assert window.docked and window.visible, 'Primary Viewport did not dock into native MainWindow'
    window.focus()
    await frames(5)
    await asyncio.wait_for(next_viewport_frame_async(window.viewport_api, 1), 15)


async def _settle(extension):
    # Dispatcher completion is separate from delivery of rendered viewport frames.
    deadline = asyncio.get_running_loop().time() + 90
    next_marker = asyncio.get_running_loop().time() + 15
    _trace('action_wait_started', extension)
    while asyncio.get_running_loop().time() < deadline:
        await frames(1)
        if asyncio.get_running_loop().time() >= next_marker:
            _trace('action_still_pending', extension)
            next_marker += 15
        if not extension._tasks and extension._edit_task is None:
            assert not (extension._details and extension._details._error), extension._details._error if extension._details else ''
            if extension._session and extension._session.viewpoint and extension._session.viewpoint.snapshot:
                from omni.kit.ui_test import find_all
                await frames(5)
                previews = find_all('Issue details//Frame/**/ImageWithProvider[*]')
                assert previews, 'Native screenshot preview failed to build'
            _trace('action_finished', extension)
            return
    _trace('action_timeout', extension)
    raise AssertionError('Issue UI action did not finish within 90 seconds')


async def _button(window, text):
    from omni.kit.ui_test import find, emulate_mouse_move_and_click
    import omni.ui as ui
    await frames(5)
    await asyncio.sleep(.6)
    widget = find(f"{window}//Frame/**/Button[*].text=='{text}'")
    assert widget, f'{window}: missing button {text}'
    for panel_name in ('Issues', 'Issue details'):
        handle = ui.Workspace.get_window(panel_name)
        if handle and handle.visible:
            assert handle.docked, f'{panel_name}: panel must be docked before click'
    await widget.focus()
    widget = find(f"{window}//Frame/**/Button[*].text=='{text}'")
    assert widget, f'{window}: button disappeared after focus: {text}'
    await emulate_mouse_move_and_click(widget.center)
    for panel_name in ('Issues', 'Issue details'):
        handle = ui.Workspace.get_window(panel_name)
        if handle and handle.visible:
            assert handle.docked, f'{panel_name}: native click undocked panel'


async def _action(extension, callback, *args):
    task = extension._details._action(callback, *args)
    assert task is not None, 'Details action was disabled or failed to dispatch'
    await asyncio.wait_for(task, 90)
    await _settle(extension)


async def _surface_click(service, extension=None):
    from omni.kit.viewport.utility import get_active_viewport_window, next_viewport_frame_async
    from omni.kit.ui_test import Vec2, emulate_mouse_move_and_click
    window = get_active_viewport_window('Viewport')
    _trace('surface_focus_started', extension, service)
    window.focus()
    await frames(30)
    await asyncio.wait_for(next_viewport_frame_async(window.viewport_api, 1), 15)
    _trace('surface_frame_delivered', extension, service)
    assert await service.viewport.pick(0, 0), 'Fixture has no pickable center surface'
    _trace('surface_center_pick_passed', extension, service)
    await asyncio.sleep(.6)
    frame = window.frame
    assert window.viewport_widget.visible and frame.computed_width > 0 and frame.computed_height > 0
    point = (float(frame.screen_position_x) + float(frame.computed_width) / 2,
             float(frame.screen_position_y) + float(frame.computed_height) / 2)
    if extension:
        for panel in (extension._window, extension._details):
            if panel and panel.window.visible:
                state = _window_state(panel.window, panel.window.frame, point)
                assert state['contains_click'] is False, f'Visible {panel.window.title} covers surface click: {state}'
    _trace('surface_mouse_before', extension, service, point)
    await emulate_mouse_move_and_click(Vec2(*point))
    await frames(30)
    await asyncio.wait_for(next_viewport_frame_async(window.viewport_api, 1), 15)
    _trace('surface_mouse_delivered', extension, service, point)
    if service.viewport.is_placing:
        _trace('surface_click_did_not_resolve_placement', extension, service, point)
        raise AssertionError('Native surface click did not resolve placement; see acc-workflow-diagnostics.jsonl')


async def _scene(service):
    from omni.kit.viewport.utility import get_active_viewport_window
    await _native_dependencies()
    with Usd.EditContext(service.stage, service.stage.GetSessionLayer()):
        camera = UsdGeom.Camera.Define(service.stage, '/OmniverseKit_Persp')
        camera.MakeMatrixXform().Set(Gf.Matrix4d().SetTranslate(Gf.Vec3d(0, 0, 10)))
    UsdGeom.Cube.Define(service.stage, '/AcceptanceCube')
    UsdLux.DistantLight.Define(service.stage, '/AcceptanceLight').GetIntensityAttr().Set(3000)
    get_active_viewport_window('Viewport').viewport_api.camera_path = '/OmniverseKit_Persp'
    await _dock_primary_viewport(service)
    await frames(30)


async def _create(extension, title):
    before = extension._service.list_issues()
    await frames(5)
    # Invoke the actual list event, then deliver an actual native viewport mouse gesture.
    _trace('create_button_before', extension)
    assert extension._window.window.docked and extension._window.window.visible, 'Issues must remain visible and docked'
    await _button('Issues', 'Create issue')
    await frames(5)
    assert extension._window._placing and extension._viewport.is_placing
    _trace('create_placement_armed', extension)
    await _surface_click(extension._service, extension)
    await _settle(extension)
    assert extension._service.list_issues() == before
    assert extension._session.is_new and extension._session.record.anchor
    assert extension._window.window is not extension._details.window
    assert extension._window.window.visible and extension._details.window.visible
    assert extension._details.window.docked, 'Details did not dock separately beside the native Viewport'
    assert extension._markup.core.editing_markup is not None, 'Placement must start native Markup'
    extension._details.title.set_value(title)


def _arrow(extension, offset=0):
    # Public native Markup action; neither capture nor Markup is replaced by a double.
    # Native rect coordinates are percentages; keep distinct test arrows inside the viewport.
    shift = offset / 4
    extension._markup.core.add_element(20 + shift, 20, 70 + shift, 70, 'Arrow',
        {'Markup.Viewport.Arrow': {'color': 0xff0000ff, 'border_width': 5}, 'ArrowDirection': 1},
        color=-16776961)


def _spec(stage, path):
    layer = Sdf.Layer.CreateAnonymous()
    assert stage.GetRootLayer().GetPrimAtPath(path), f'Missing saved native evidence: {path}'
    Sdf.CreatePrimInLayer(layer, path)
    assert Sdf.CopySpec(stage.GetRootLayer(), path, layer, path), f'Could not copy saved native evidence: {path}'
    return layer.ExportToString()


def test_acc_spec_snapshot_preserves_nested_subtree():
    stage = Usd.Stage.CreateInMemory()
    path = '/Viewport_Markups/IssueEvidence_saved'
    stage.DefinePrim(path, 'Xform').SetCustomDataByKey('label', 'saved evidence')
    child = stage.DefinePrim(path + '/Arrow', 'Scope')
    color = child.CreateAttribute('color', Sdf.ValueTypeNames.String)
    color.Set('red')
    before = stage.GetRootLayer().ExportToString()

    original = _spec(stage, path)
    copied = Sdf.Layer.CreateAnonymous()
    assert copied.ImportFromString(original)
    assert copied.GetPrimAtPath(path).customData['label'] == 'saved evidence'
    assert copied.GetAttributeAtPath(path + '/Arrow.color').default == 'red'
    assert stage.GetRootLayer().ExportToString() == before, 'Evidence comparison mutated the source'
    assert _spec(stage, path) == original

    color.Set('blue')
    assert _spec(stage, path) != original, 'Evidence comparison ignored a nested annotation change'


def _png(record, name, annotated=False):
    (ROOT / 'verification' / name).write_bytes(record.snapshot)
    from PIL import Image
    assert record.snapshot.startswith(b'\x89PNG\r\n\x1a\n')
    image = Image.open(io.BytesIO(record.snapshot)).convert('RGB')
    assert image.width > 100 and image.height > 100
    colors = set(image.getdata())
    assert len(colors) > 20, 'Screenshot lacks rendered scene detail'
    if annotated:
        assert any(r > 240 and g < 30 and b < 30 for r, g, b in colors), 'Native red arrow is absent'


def _comment_evidence_trace(extension, phase, **records):
    stage, core = extension._service.stage, extension._markup.core
    prefix = ROOT / 'verification' / f'acc-comment-{phase}'
    stage.GetRootLayer().Export(str(prefix.with_suffix('.usda')))
    def elements(prims):
        return {str(prim.GetPath()): {attr.GetName(): str(attr.Get()) for attr in prim.GetAttributes()}
                for prim in prims if not prim.IsA(UsdGeom.Camera) and not prim.HasAttribute('projection')}
    state = {'phase': phase, 'current': core.current_markup.path if core.current_markup else None,
             'editing': core.editing_markup.path if core.editing_markup else None,
             'current_elements': elements(core.get_markup_elements()), 'records': {}}
    for name, record in records.items():
        prefix.with_name(prefix.name + '-' + name + '.png').write_bytes(record.snapshot)
        prim = stage.GetPrimAtPath(record.markup_path)
        state['records'][name] = {'id': record.id, 'markup_path': record.markup_path,
                                  'elements': elements(prim.GetChildren()) if prim else None}
    prefix.with_suffix('.json').write_text(json.dumps(state, indent=2), encoding='utf-8')
    _trace('comment-' + phase, extension)


async def _discard(extension):
    await _button('Issue details', 'Cancel')
    await _button('Unsaved issue changes', 'Discard')
    await _settle(extension)
    assert extension._session is None


async def _close(extension):
    from test_ui import close_controller
    await close_controller(extension)
    shutdown = getattr(extension, '_shutdown_task', None)
    if shutdown:
        await asyncio.wait_for(shutdown, 90)


async def test_acc_create_save_clean_native_evidence(service):
    from test_creation import exercise_creation
    await exercise_creation(service, save=True)


async def test_acc_create_cancel_removes_native_draft(service):
    from test_creation import exercise_creation
    await exercise_creation(service, save=False)


async def test_acc_dirty_native_close_and_switch_save_discard_stay(service):
    from test_ui import controller_for
    from issues_tag.model import Status
    await _native_dependencies()
    from omni.kit.ui_test import find_all
    first = service.create_issue('First saved issue')
    second = service.create_issue('Second saved issue')
    extension = controller_for(service)
    try:
        extension._window.select_issue(first)
        await _settle(extension)
        original = service.get_issue(first)
        extension._details.title.set_value('Draft title')
        extension._details.description.set_value('Draft description')
        extension._details.comment.set_value('Draft comment')
        extension._session.update(status=Status.IN_PROGRESS)
        extension._details.sync()
        extension._details.refresh()
        await frames(5)

        def draft_state():
            details, session = extension._details, extension._session
            choices = find_all('Issue details//Frame/**/ComboBox[*]')
            assert len(choices) == 2, 'Status/type controls failed to build'
            return (session.record, session.comment_text,
                    details.title.as_string, details.description.as_string, details.comment.as_string,
                    tuple(choice.model.get_item_value_model().as_int for choice in choices))

        before_close_stay = draft_state()
        assert (before_close_stay[0].title, before_close_stay[0].description, before_close_stay[0].status,
                before_close_stay[1]) == ('Draft title', 'Draft description', Status.IN_PROGRESS, 'Draft comment')
        extension._details.window.visible = False
        await _button('Unsaved issue changes', 'Stay')
        await _settle(extension)
        assert extension._session.record.id == first and extension._details.window.visible
        assert service.get_issue(first) == original
        assert draft_state() == before_close_stay, 'Native-close Stay lost staged record, comment or UI values'
        assert extension._session.dirty
        before_switch_stay = draft_state()
        extension._window.select_issue(second)
        await _button('Unsaved issue changes', 'Stay')
        await _settle(extension)
        assert extension._session.record.id == first and service.get_issue(first) == original
        assert draft_state() == before_switch_stay, 'Issue-switch Stay lost staged record, comment or UI values'
        assert extension._session.dirty and extension._details.window.visible
        extension._window.select_issue(second)
        await _button('Unsaved issue changes', 'Discard')
        await _settle(extension)
        assert extension._session.record.id == second and service.get_issue(first) == original
        extension._window.select_issue(first)
        await _settle(extension)
        extension._details.title.set_value('Accepted title')
        extension._details.description.set_value('Accepted description')
        extension._details.comment.set_value('Accepted comment')
        extension._session.update(status=Status.RESOLVED)
        extension._window.select_issue(second)
        await _button('Unsaved issue changes', 'Save')
        await _settle(extension)
        saved = service.get_issue(first)
        assert (saved.title, saved.description, saved.status) == ('Accepted title', 'Accepted description', Status.RESOLVED)
        assert [c.text for c in saved.comments] == ['Accepted comment']
        assert extension._session.record.id == second
        extension._details.title.set_value('Discard native close')
        extension._details.window.visible = False
        await _button('Unsaved issue changes', 'Discard')
        await _settle(extension)
        assert extension._session is None and service.get_issue(second).title != 'Discard native close'
        extension._window.select_issue(first)
        await _settle(extension)
        extension._details.title.set_value('Saved native close')
        extension._details.window.visible = False
        await _button('Unsaved issue changes', 'Save')
        await _settle(extension)
        assert extension._session is None and service.get_issue(first).title == 'Saved native close'
    finally:
        await _close(extension)


async def test_acc_native_annotation_and_replacement_save_cancel(service):
    from test_ui import controller_for
    await _scene(service)
    extension = controller_for(service)
    try:
        await _create(extension, 'Saved native evidence')
        _arrow(extension)
        await _button('Issue details', 'Save')
        await _settle(extension)
        issue = service.list_issues()[0]
        original = service.store.get_viewpoint(issue.initial_viewpoint_id)
        original_spec = _spec(service.stage, original.markup_path)
        _png(original, 'acc-initial-annotated.png', True)
        for callback_name in ('on_annotate', 'on_replace'):
            extension._window.select_issue(issue.id)
            await _settle(extension)
            await _action(extension, getattr(extension._details, callback_name))
            draft = extension._session.viewpoint
            assert draft.id != original.id and draft.markup_path != original.markup_path
            if callback_name == 'on_annotate':
                _arrow(extension, 20)
            await _discard(extension)
            assert service.get_issue(issue.id) == issue
            assert service.store.get_viewpoint(original.id) == original
            assert _spec(service.stage, original.markup_path) == original_spec
            assert not service.stage.GetPrimAtPath(draft.markup_path), 'Discard left owned native evidence'
        extension._window.select_issue(issue.id)
        await _settle(extension)
        await _action(extension, extension._details.on_annotate)
        annotated_id = extension._session.viewpoint.id
        _arrow(extension, 40)
        await _button('Issue details', 'Save')
        await _settle(extension)
        assert service.get_issue(issue.id).initial_viewpoint_id == annotated_id
        accepted = service.store.get_viewpoint(annotated_id)
        _png(accepted, 'acc-edited-annotation.png', True)
        assert accepted.snapshot != original.snapshot
        assert _spec(service.stage, original.markup_path) == original_spec
        extension._window.select_issue(issue.id)
        await _settle(extension)
        await _action(extension, extension._details.on_replace)
        replacement = extension._session.viewpoint
        assert replacement.id != annotated_id
        await _button('Issue details', 'Save')
        await _settle(extension)
        assert service.get_issue(issue.id).initial_viewpoint_id == replacement.id
        assert service.store.get_viewpoint(replacement.id).snapshot == replacement.snapshot
        _png(replacement, 'acc-replaced-screenshot.png')
        assert service.store.get_viewpoint(original.id) == original
        assert _spec(service.stage, original.markup_path) == original_spec
    finally:
        await _close(extension)


async def test_acc_filtered_parent_related_comment_and_bcf_journey(service):
    from test_ui import controller_for
    from issues_tag.elements import reference_for_prim, attachment_state
    from issues_tag.bcf import export_document, write_bcf, read_bcf, plan_import, apply_import
    from issues_tag.model import Status
    await _scene(service)
    from omni.kit.ui_test import find_all
    building_path = ROOT / 'verification' / 'acc-source-building.usda'
    source_layer = Sdf.Layer.FindOrOpen(str(building_path))
    if source_layer:
        source_layer.Clear()
        source_stage = Usd.Stage.Open(source_layer)
    else:
        source_stage = Usd.Stage.CreateNew(str(building_path))
    UsdGeom.Xform.Define(source_stage, '/Building')
    UsdGeom.Cube.Define(source_stage, '/Building/Related').AddTranslateOp().Set(Gf.Vec3d(5, 0, 0))
    source_stage.SetDefaultPrim(source_stage.GetPrimAtPath('/Building'))
    source_stage.GetRootLayer().Save()
    source_bytes = building_path.read_bytes()
    source_spec = source_stage.GetRootLayer().ExportToString()
    building = service.stage.DefinePrim('/ReferencedBuilding', 'Xform')
    building.GetReferences().AddReference(str(building_path))
    service.create_type('Quality')
    extension = controller_for(service)
    closed = False
    try:
        extension._window.author.set_value('Acceptance reviewer')
        await _button('Issues', 'Apply')
        await _settle(extension)
        assert service.author_name == 'Acceptance reviewer'
        extension._window.search.set_value('No matching saved issue')
        extension._window.status_filter = Status.CLOSED.value
        extension._window.type_filter = 'Quality'
        extension._window.refresh()
        await frames(10)
        assert not extension._window.visible_issue_ids and extension._viewport.filtered_issue_ids == frozenset()
        await _create(extension, 'Discoverable new issue')
        _arrow(extension)
        await _button('Issue details', 'Save')
        await _settle(extension)
        issue = service.list_issues()[0]
        assert issue.author == 'Acceptance reviewer'
        assert issue.id in extension._window.visible_issue_ids
        assert extension._window.selected_issue_id == issue.id
        assert extension._window.search.as_string == ''
        await frames(10)
        items = [item for item in extension._viewport._items if item.viewport_api == extension._viewport.viewport]
        assert items and any(issue.id in item.visible_issue_ids for item in items)
        extension._window.search.set_value('No matching saved issue')
        await frames(10)
        assert not any(item.visible_issue_ids for item in items), 'Filtered saved pin remained visible'
        extension._window.clear_filters()
        extension._window.select_issue(issue.id)
        await _settle(extension)
        initial = service.store.get_viewpoint(issue.initial_viewpoint_id)
        initial_spec = _spec(service.stage, initial.markup_path)
        draft = extension._session
        extension._details.title.set_value('Staged title survives review recall')
        assert extension._details._draft_state.text == 'Unsaved issue edits. Save issue, then save scene.'
        original_related = issue.related_elements
        assert issue.anchor.element in original_related
        related = reference_for_prim(service.stage, '/ReferencedBuilding/Related')
        assert related not in original_related
        service._context.get_selection().set_selected_prim_paths([related.prim_path], False)
        await _action(extension, extension._details.on_add_related)
        assert extension._session.record.related_elements == original_related + (related,)
        assert service.get_issue(issue.id) == issue
        await _action(extension, extension._details.on_remove_related, related)
        assert extension._session.record.related_elements == original_related
        assert extension._session.record.anchor == issue.anchor and service.get_issue(issue.id) == issue
        await _action(extension, extension._details.on_add_related)
        viewport = service.viewport.viewport
        camera = UsdGeom.Camera(service.stage.GetPrimAtPath(viewport.camera_path))
        before_focus = camera.ComputeLocalToWorldTransform(viewport.time)
        await _action(extension, extension._details.on_focus_related)
        for _ in range(120):
            await frames(1)
            camera = UsdGeom.Camera(service.stage.GetPrimAtPath(viewport.camera_path))
            after_focus = camera.ComputeLocalToWorldTransform(viewport.time)
            if not Gf.IsClose(before_focus, after_focus, 1e-6):
                break
        assert not Gf.IsClose(before_focus, after_focus, 1e-6), 'Focus related did not change viewport camera framing'
        staged_record = draft.record
        await _button('Issue details', 'Open review view')
        await _settle(extension)
        for _ in range(120):
            await frames(1)
            camera = UsdGeom.Camera(service.stage.GetPrimAtPath(viewport.camera_path))
            recalled_pose = camera.ComputeLocalToWorldTransform(viewport.time)
            if Gf.IsClose(before_focus, recalled_pose, 1e-6):
                break
        assert Gf.IsClose(before_focus, recalled_pose, 1e-6), 'Open review view did not restore the saved world pose'
        recalled_context = service.viewport.capture()
        assert recalled_context.selection == initial.selection
        assert all(dict(recalled_context.visibility).get(path) == state for path, state in initial.visibility)
        assert recalled_context.clipping_planes == initial.clipping_planes
        assert recalled_context.section_state == initial.section_state
        assert extension._session is draft and draft.record == staged_record
        assert draft.record.title == 'Staged title survives review recall' and draft.dirty
        assert extension._details._draft_state.text == 'Unsaved issue edits. Save issue, then save scene.'
        assert service.get_issue(issue.id) == issue
        assert service.store.get_viewpoint(initial.id) == initial
        assert _spec(service.stage, initial.markup_path) == initial_spec
        await frames(10)
        await _action(extension, extension._details.on_capture_comment)
        await _action(extension, extension._details.on_annotate_comment)
        _arrow(extension, 20)
        extension._details.comment.set_value('Annotated comment from actual details actions')
        await _action(extension, extension._details.on_add_comment)
        comment = extension._session.record.comments[-1]
        comment_view = extension._session.comment_viewpoints[comment.id]
        assert not service.get_issue(issue.id).comments
        assert extension._session.viewpoint.id == initial.id
        await frames(5)
        choices = find_all('Issue details//Frame/**/ComboBox[*]')
        assert len(choices) == 2, 'Status/type controls failed to build'
        choices[0].model.get_item_value_model().set_value(tuple(Status).index(Status.IN_PROGRESS))
        choices[1].model.get_item_value_model().set_value(extension._details.types.index('Quality'))
        assert extension._session.record.status == Status.IN_PROGRESS
        assert extension._session.record.issue_type == 'Quality'
        await _button('Issue details', 'Save')
        await _settle(extension)
        saved = service.get_issue(issue.id)
        assert (saved.status, saved.issue_type) == (Status.IN_PROGRESS, 'Quality')
        assert saved.author == saved.comments[-1].author == 'Acceptance reviewer'
        assert saved.comments[-1].viewpoint_id == comment_view.id and related in saved.related_elements
        _png(service.store.get_viewpoint(comment_view.id), 'acc-comment-annotated.png', True)
        comment_spec = _spec(service.stage, comment_view.markup_path)
        extension._window.select_issue(issue.id)
        await _settle(extension)
        await _action(extension, extension._details.on_annotate_comment, comment.id)
        draft = extension._session.comment_viewpoints[comment.id]
        _arrow(extension, 40)
        await _discard(extension)
        assert service.get_issue(issue.id) == saved
        assert service.store.get_viewpoint(comment_view.id) == comment_view
        assert _spec(service.stage, comment_view.markup_path) == comment_spec
        assert not service.stage.GetPrimAtPath(draft.markup_path)
        extension._window.select_issue(issue.id)
        await _settle(extension)
        copy_for_edit = extension._markup.copy_for_edit
        async def observe_copy(record):
            copied = await copy_for_edit(record)
            _comment_evidence_trace(extension, 'after-copy', saved=record, draft=copied)
            return copied
        with patch.object(extension._markup, 'copy_for_edit', observe_copy):
            await _action(extension, extension._details.on_annotate_comment, comment.id)
        draft_comment = extension._session.comment_viewpoints[comment.id]
        _comment_evidence_trace(extension, 'after-begin', saved=comment_view, draft=draft_comment)
        _arrow(extension, 60)
        _comment_evidence_trace(extension, 'before-save', saved=comment_view, draft=draft_comment)
        accepted_comment_id = draft_comment.id
        await _button('Issue details', 'Save')
        await _settle(extension)
        saved = service.get_issue(issue.id)
        assert saved.comments[-1].viewpoint_id == accepted_comment_id
        accepted_comment = service.store.get_viewpoint(accepted_comment_id)
        _comment_evidence_trace(extension, 'after-save', saved=comment_view, accepted=accepted_comment)
        _png(accepted_comment, 'acc-comment-edited.png', True)
        accepted_comment_spec = _spec(service.stage, accepted_comment.markup_path)
        UsdGeom.Cube(service.stage.GetPrimAtPath('/AcceptanceCube')).GetSizeAttr().Set(3)
        assert attachment_state(service.stage, saved.anchor) == 'needs_review'
        extension._window.select_issue(issue.id)
        await _settle(extension)
        task = extension._details._action(extension._details.on_reattach)
        await frames(5)
        assert extension._viewport.is_placing
        await _surface_click(service, extension)
        await asyncio.wait_for(task, 90)
        assert attachment_state(service.stage, service.get_issue(issue.id).anchor) == 'needs_review'
        assert attachment_state(service.stage, extension._session.record.anchor) == 'verified'
        await _button('Issue details', 'Save')
        await _settle(extension)
        saved = service.get_issue(issue.id)
        assert saved.initial_viewpoint_id == initial.id
        assert service.store.get_viewpoint(initial.id) == initial
        assert _spec(service.stage, initial.markup_path) == initial_spec
        parent_path = ROOT / 'verification' / 'acc-parent-saved.usda'
        assert service.stage.GetRootLayer().Export(str(parent_path))
        evidence = {view_id: service.store.get_viewpoint(view_id) for view_id in (initial.id, accepted_comment_id)}
        await _close(extension)
        closed = True
        opened, error = await service._context.open_stage_async(str(parent_path))
        assert opened, error
        await frames(30)
        assert service.get_issue(saved.id) == saved and saved.number > 0
        assert [service.store.get_viewpoint(view_id) for view_id in evidence] == list(evidence.values())
        assert _spec(service.stage, initial.markup_path) == initial_spec
        assert _spec(service.stage, accepted_comment.markup_path) == accepted_comment_spec
        assert service.stage.GetPrimAtPath('/ReferencedBuilding/Related'), 'Parent lost its building reference'
        assert source_stage.GetRootLayer().ExportToString() == source_spec
        assert building_path.read_bytes() == source_bytes, 'Referenced source file was modified'
        assert not source_stage.GetRootLayer().dirty, 'Referenced source layer was edited in memory'
        assert not source_stage.GetRootLayer().GetPrimAtPath('/Issues'), 'Issue records leaked into the source building'
        bcf_path = ROOT / 'verification' / 'acc-parent-exchange.bcf'
        write_bcf(export_document(service.store), bcf_path)
        document = read_bcf(bcf_path)
        incoming = next(record for record in document.issues if record.id == saved.id)
        assert (incoming.title, incoming.issue_type, incoming.status, incoming.description, incoming.comments) == (
            saved.title, saved.issue_type, saved.status, saved.description, saved.comments)
        assert all(any(view.id == view_id and view.snapshot == expected.snapshot for view in document.viewpoints)
                   for view_id, expected in evidence.items())
        apply_import(plan_import(document, service.store), {}, service)
        first_import = service.get_issue(saved.id)
        repeated = apply_import(plan_import(document, service.store), {}, service)
        assert (repeated.created, repeated.updated, repeated.comments_added, repeated.viewpoints_added) == (0, 0, 0, 0)
        assert len(service.list_issues()) == 1 and service.get_issue(saved.id) == first_import
        assert first_import.number == saved.number
        assert len({c.id for c in first_import.comments}) == len(saved.comments)
        assert building_path.read_bytes() == source_bytes
    finally:
        if not closed:
            await _close(extension)


async def _disable_runtime():
    from issues_tag.extension import IssuesExtension
    captured = []
    original = IssuesExtension.on_shutdown
    def observe(instance):
        controller = instance._controller
        result = original(instance)
        # Kit clears IExt.__dict__ immediately after this callback returns.
        # Retain the task here, before the manager removes its owning attributes.
        captured.append((controller, getattr(controller, '_shutdown_task', None)))
        return result
    with patch.object(IssuesExtension, 'on_shutdown', observe):
        enable_extension('issues.tag', False)
    for instance, shutdown in captured:
        if shutdown:
            await asyncio.wait_for(shutdown, 90)
    await frames(10)
    return [instance for instance, shutdown in captured]


async def _enable_runtime():
    # Read the SDK's Python lifecycle registry. Enabling reloads the extension's
    # modules, so patching the pre-enable class would observe the wrong class.
    from omni.ext._impl import _internal
    assert enable_extension('issues.tag')
    ext_id = APP.get_extension_manager().get_enabled_extension_id('issues.tag')
    started = _internal._extensions[ext_id]._started_extensions
    instances = [instance for instance, module in started if module == 'issues_tag']
    assert len(instances) == 1, 'Runtime extension did not restart exactly once'
    await frames(10)
    return instances[0]._controller


async def test_acc_runtime_disable_drains_native_draft_before_reenable():
    import omni.usd
    await _native_dependencies()
    await _disable_runtime()
    extension = None
    try:
        # Stage replacement occurs only after the previous real runtime shutdown drains.
        await omni.usd.get_context().new_stage_async()
        await frames(10)
        extension = await _enable_runtime()
        service = extension._service
        await _scene(service)
        extension.show()
        await _create(extension, 'Unsaved draft before disable')
        draft = extension._session.viewpoint
        _arrow(extension)
        await _button('Issue details', 'Save')
        await _settle(extension)
        issue = service.list_issues()[0]
        saved = service.store.get_viewpoint(issue.initial_viewpoint_id)
        saved_spec = _spec(service.stage, saved.markup_path)
        from issues_tag.store import encode
        saved_issue_data, saved_view_data = encode(issue), encode(saved)
        stage = service.stage
        extension._window.select_issue(issue.id)
        await _settle(extension)
        await _action(extension, extension._details.on_annotate)
        draft = extension._session.viewpoint
        _arrow(extension, 30)
        # Disable during an actual dispatched native snapshot, with no replacement boundary.
        action = extension._details._action(extension._details.on_save)
        assert action is not None
        await frames(1)
        assert extension._edit_task is not None and not action.done(), 'Native Save must be pending at disable'
        assert extension in await _disable_runtime()
        assert action.done() and getattr(extension, '_service', None) is None and getattr(extension, '_viewport', None) is None
        from issues_tag.store import IssueStore, encode
        store = IssueStore(stage)
        assert encode(store.get_issue(issue.id)) == saved_issue_data, 'Saved issue content changed during disable'
        assert encode(store.get_viewpoint(saved.id)) == saved_view_data, 'Saved evidence content changed during disable'
        assert _spec(stage, saved.markup_path) == saved_spec
        assert not stage.GetPrimAtPath(draft.markup_path)
        extension = await _enable_runtime()
        assert encode(extension._service.get_issue(issue.id)) == saved_issue_data
        assert encode(extension._service.store.get_viewpoint(saved.id)) == saved_view_data
        extension.show()
        extension._window.select_issue(issue.id)
        await _settle(extension)
        assert encode(extension._session.record) == saved_issue_data and not extension._session.dirty
        from omni.kit.markup.core import get_instance
        native_core = get_instance()
        assert native_core is not None and native_core.editing_markup is None
    finally:
        await _disable_runtime()
        await _enable_runtime()
