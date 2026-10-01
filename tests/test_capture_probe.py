"""Explicit capture diagnostics: select Case capture_probe, never part of Case all."""
import asyncio
import importlib
import json
import os
from datetime import datetime, timezone
from uuid import uuid4

import omni.usd
from pxr import Gf, UsdGeom

from verify_kit import APP, ROOT, enable_extension, frames, qualify_runtime


def _milestone(probe, cycle, phase, stage=None, viewport=None):
    value = {'probe': probe, 'cycle': cycle, 'phase': phase,
             'stage': stage.GetRootLayer().identifier if stage else None,
             'updated_at': datetime.now(timezone.utc).isoformat()}
    if viewport is not None:
        value.update(camera_path=str(viewport.camera_path), resolution=list(viewport.resolution))
    destination = ROOT / 'verification' / 'capture-probe.json'
    temporary = destination.with_suffix('.json.tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    from verification_progress import replace_progress
    replace_progress(temporary, destination)
    print('ISSUES_CAPTURE_PROBE', json.dumps(value), flush=True)


async def _prepare_camera(stage):
    from omni.kit.viewport.utility import get_active_viewport_window, next_viewport_frame_async
    window = get_active_viewport_window('Viewport')
    assert window and window.visible, 'Capture probe requires a visible primary viewport'
    camera = UsdGeom.Camera.Define(stage, '/CaptureProbeCamera')
    camera.AddTranslateOp().Set(Gf.Vec3d(0, 0, 10))
    UsdGeom.Cube.Define(stage, '/CaptureProbeCube')
    window.viewport_api.camera_path = camera.GetPath()
    window.focus()
    await asyncio.wait_for(next_viewport_frame_async(window.viewport_api, 1), 30)


async def _new_scene(probe, cycle, simple_scene=True):
    context = omni.usd.get_context()
    _milestone(probe, cycle, 'before_stage', context.get_stage())
    await context.new_stage_async()
    stage = context.get_stage()
    _milestone(probe, cycle, 'after_stage', stage)
    await frames(5)  # Match the ordinary scene fixture before comparing capture paths.
    if simple_scene:
        await _prepare_camera(stage)
    _milestone(probe, cycle, 'scene_ready', stage)
    return stage


async def _native_capture(core, probe, cycle, stage, restore_session=False, cancellation=None):
    from omni.kit.markup.core import MarkupChangeCallbacks
    from omni.kit.viewport.utility import get_active_viewport_window
    # The cancellation test explicitly readies Core, then the adapter readies it again.
    await frames(16)
    name = 'NativeCaptureProbe_' + uuid4().hex
    created = asyncio.get_running_loop().create_future()
    markup = None

    def on_created(*args):
        owned = core.get_markup(name)
        if owned and owned.thumbnail_data and not created.done():
            if cancellation is not None:
                cancellation['caller'].cancel()
            created.set_result(owned)

    callback = MarkupChangeCallbacks(on_markup_created=on_created)
    core.register_callback(callback)
    if restore_session:
        stage.SetEditTarget(stage.GetSessionLayer())
        stage.SetEditTarget(stage.GetRootLayer())
    try:
        deadline = asyncio.get_running_loop().time() + 30
        _milestone(probe, cycle, 'before_capture', stage)
        core.create_markup('/Viewport_Markups/' + name)
        markup = core.get_markup(name)
        markup = await asyncio.wait_for(created, max(0, deadline - asyncio.get_running_loop().time()))
        _milestone(probe, cycle, 'thumbnail_callback_complete', stage)
        # Public SDK settling convention; this is not a GPU completion fence.
        await asyncio.wait_for(markup.wait(), max(0, deadline - asyncio.get_running_loop().time()))
        _milestone(probe, cycle, 'public_wait_complete', stage)
        assert markup.thumbnail_data, 'Native capture did not produce a thumbnail'
        if cancellation is not None and cancellation['requested']:
            raise asyncio.CancelledError()
    finally:
        try:
            core.deregister_callback(callback)
            window = get_active_viewport_window('Viewport')
            viewport = window.viewport_api if window else None
            if markup and core.editing_markup == markup:
                _milestone(probe, cycle, 'before_end_edit', stage, viewport)
                core.end_edit_markup(markup, save=True, update_thumbnail=False)
                _milestone(probe, cycle, 'after_end_edit', stage, viewport)
            if markup and core.current_markup == markup:
                core.unlock_camera()
                core.current_markup = None
                _milestone(probe, cycle, 'after_current_none', stage, viewport)
        finally:
            if restore_session:
                stage.SetEditTarget(stage.GetSessionLayer())
    assert core.current_markup is None and core.editing_markup is None
    _milestone(probe, cycle, 'after_capture', stage)


async def _cancel_native_capture(core, probe, cycle, stage, restore_session):
    cancellation = {'caller': None, 'requested': False}
    async def caller():
        owned = asyncio.create_task(_native_capture(core, probe, cycle, stage, restore_session, cancellation))
        try:
            await asyncio.shield(owned)
        except asyncio.CancelledError:
            cancellation['requested'] = True
            while not owned.done():
                try:
                    await asyncio.shield(owned)
                except asyncio.CancelledError:
                    continue
            if not owned.cancelled():
                owned.result()
            raise
    task = cancellation['caller'] = asyncio.create_task(caller())
    try:
        await task
    except asyncio.CancelledError:
        assert cancellation['requested'], 'Native callback did not request cancellation'
    else:
        raise AssertionError('Native creation callback did not cancel the caller')
    assert core.current_markup is None and core.editing_markup is None
    _milestone(probe, cycle, 'after_cancel', stage)


async def _native_probe(replace_scene, simple_scene=True, issues_enabled=False, restore_session=False, cancel_capture=False):
    probe = 'native_scene_replacement' if replace_scene else 'native_stable_scene'
    if not simple_scene:
        probe += '_empty_default_scene'
    if issues_enabled:
        probe += '_issues_enabled'
    if restore_session:
        probe += '_session_target'
    if cancel_capture:
        probe += '_cancelled'
    _milestone(probe, 0, 'dependencies')
    enable_extension('issues.tag', issues_enabled)
    assert APP.get_extension_manager().is_extension_enabled('issues.tag') == issues_enabled
    assert enable_extension('omni.kit.markup.core')
    assert enable_extension('omni.kit.tool.markup')
    core = importlib.import_module('omni.kit.markup.core').get_instance()
    assert core is not None
    stage = await _new_scene(probe, 0, simple_scene)
    for cycle in range(5):
        if cancel_capture:
            await _cancel_native_capture(core, probe, cycle, stage, restore_session)
        else:
            await _native_capture(core, probe, cycle, stage, restore_session)
        if replace_scene:
            stage = await _new_scene(probe, cycle, simple_scene)
        else:
            assert omni.usd.get_context().get_stage() == stage
    _milestone(probe, cycle, 'complete', stage)


async def test_native_capture_stable_scene():
    await _native_probe(replace_scene=False)


async def test_native_capture_then_scene_replacement_repeated():
    await _native_probe(replace_scene=True)


async def test_native_capture_then_empty_scene_replacement_repeated():
    await _native_probe(replace_scene=True, simple_scene=False)


async def test_native_capture_with_issues_then_empty_scene_replacement_repeated():
    await _native_probe(replace_scene=True, simple_scene=False, issues_enabled=True)


async def test_native_capture_with_session_target_then_scene_replacement_repeated():
    await _native_probe(replace_scene=True, simple_scene=False, issues_enabled=True, restore_session=True)


async def test_native_cancel_then_scene_replacement_repeated():
    await _native_probe(replace_scene=True, simple_scene=False, issues_enabled=True, restore_session=True, cancel_capture=True)


async def _markup_prelude_then_native_cancel(tool_enabled):
    """Match the first eleven Issues Markup tests, then vary native Tool only.

    This is an Issues-enabled prelude and native capture diagnostic, not a
    native-only baseline. Run each arm in a fresh process. The Tool-enabled arm
    must reproduce the fault before a Tool-disabled pass supports a conclusion.
    """
    import test_markup as markup_tests
    from test_persistence import service_for_new_scene
    prelude = (
        'test_evidence_rejects_secondary_viewport_before_mutation',
        'test_initial_view_can_start_markup',
        'test_annotation_rejects_overlapping_ownership',
        'test_annotation_releases_navigation',
        'test_failed_annotation_begin_releases_vendor_edit',
        'test_stale_annotation_releases_owner_without_touching_new_scene',
        'test_annotated_comment_reopens_editably',
        'test_capture_stage_change_discards_result',
        'test_capture_preserves_replacement_vendor_owner',
        'test_finish_preserves_replacement_vendor_owner',
        'test_capture_camera_matches_view_after_markup_activation',
    )
    probe = 'markup_prelude_native_cancel_tool_' + ('on' if tool_enabled else 'off')
    manager = APP.get_extension_manager()
    for index, name in enumerate(prelude):
        _milestone(probe, index, 'prelude_fixture_start:' + name, omni.usd.get_context().get_stage())
        service = await service_for_new_scene()
        for dependency in ('omni.kit.markup.core', 'omni.kit.tool.markup'):
            assert enable_extension(dependency), 'Cannot enable private Markup dependency'
        qualify_runtime()
        _milestone(probe, index, 'prelude_start:' + name, service.stage)
        await getattr(markup_tests, name)(service)
        qualify_runtime()
        _milestone(probe, index, 'prelude_end:' + name, service.stage)
    _milestone(probe, 0, 'fresh_fixture_start', omni.usd.get_context().get_stage())
    service = await service_for_new_scene()
    _milestone(probe, 0, 'fresh_fixture_complete', service.stage)
    assert enable_extension('omni.kit.markup.core')
    enable_extension('omni.kit.tool.markup', tool_enabled)
    qualify_runtime()
    core = importlib.import_module('omni.kit.markup.core').get_instance()
    assert core is not None
    stage = service.stage
    for cycle in range(5):
        assert manager.is_extension_enabled('issues.tag'), 'Issues must stay enabled in both arms'
        assert manager.is_extension_enabled('omni.kit.markup.core'), 'Core must stay enabled in both arms'
        assert manager.is_extension_enabled('omni.kit.tool.markup') == tool_enabled, 'Tool state changed before capture'
        await _cancel_native_capture(core, probe, cycle, stage, restore_session=True)
        stage = await _new_scene(probe, cycle, simple_scene=False)
    _milestone(probe, cycle, 'complete', stage)


async def test_markup_prelude_native_cancel_tool_on():
    await _markup_prelude_then_native_cancel(tool_enabled=True)


async def test_markup_prelude_native_cancel_tool_off():
    await _markup_prelude_then_native_cancel(tool_enabled=False)


async def test_issues_capture_cancellation_without_scene_replacement(service):
    from test_markup import test_creation_callback_cancellation_releases_markup_and_edit_target
    probe = 'issues_cancellation_stable_scene'
    _milestone(probe, 0, 'dependencies', service.stage)
    assert enable_extension('omni.kit.markup.core')
    assert enable_extension('omni.kit.tool.markup')
    stage = service.stage
    await _prepare_camera(stage)
    for cycle in range(5):
        _milestone(probe, cycle, 'before_capture', stage)
        await test_creation_callback_cancellation_releases_markup_and_edit_target(service)
        _milestone(probe, cycle, 'after_cancel', stage)
        assert service.stage == stage, 'Cancellation probe changed scenes'
        assert not service.list_issues(), 'Cancelled capture created an issue'
    _milestone(probe, cycle, 'complete', stage)
