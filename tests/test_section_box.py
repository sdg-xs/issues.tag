from verify_kit import enable_extension
"""Acceptance coverage for the installed Section Box public integration."""

import importlib

import omni.kit.app
from omni.kit.viewport.utility import get_active_viewport
from pxr import Gf, UsdGeom

from verify_kit import frames


def _close_values(actual, expected, tolerance=1e-6):
    assert len(actual) == len(expected)
    assert all(abs(float(a) - float(b)) <= tolerance for a, b in zip(actual, expected)), (actual, expected)


async def test_section_box_controls_and_planes_restore_with_issue(service):
    from issues_tag.viewport import ENABLED, PLANES, ViewportAdapter, flatten

    manager = omni.kit.app.get_app().get_extension_manager()
    was_enabled = manager.is_extension_enabled('section.box')
    old_adapter = service.viewport
    adapter = None
    state = None
    previous = None
    try:
        enable_extension('section.box', True)
        assert manager.is_extension_enabled('section.box'), 'The installed section.box extension must activate'
        section_box = importlib.import_module('section_box')
        from section_box.model import Face, SectionBox

        viewport = get_active_viewport(usd_context_name=None)
        assert viewport and viewport.stage == service.stage, 'Section Box needs the active viewport for the issue scene'
        camera = UsdGeom.Camera.Define(service.stage, '/SectionReviewCamera')
        camera.AddTranslateOp().Set(Gf.Vec3d(0, 0, 20))
        viewport.camera_path = camera.GetPath()
        UsdGeom.Cube.Define(service.stage, '/SectionReviewModel')
        await frames(10)

        state = section_box.get_runtime_state()
        assert state is not None
        state.sync_stage()
        assert state.stage == service.stage
        previous = state.snapshot
        adapter = ViewportAdapter(service, viewport)
        service.viewport = adapter
        transform = Gf.Matrix4d().SetRotate(Gf.Rotation(Gf.Vec3d(0, 1, 0), 25))
        transform.SetTranslateOnly(Gf.Vec3d(2, 3, 4))
        saved_box = SectionBox(transform, Gf.Vec3d(12, 10, 8), frozenset((Face.MIN_X, Face.MAX_X, Face.MIN_Z)))
        state.edit(box=saved_box, enabled=True)
        await frames(10)
        render = service.stage.GetPrimAtPath(viewport.render_product_path)
        assert render and render.GetAttribute(ENABLED).Get(), 'Enabled Section Box must reach the RTX render product'
        expected_planes = tuple(tuple(-float(value) for value in plane) for plane in saved_box.active_planes())
        assert len(expected_planes) == 3
        actual_planes = adapter.clipping_planes(viewport)
        assert len(actual_planes) == len(expected_planes)
        for actual, expected in zip(actual_planes, expected_planes):
            _close_values(actual, expected)

        saved = adapter.capture()
        assert saved.section_state['enabled'] is True
        assert set(saved.section_state['faces']) == {face.name for face in saved_box.faces}
        _close_values(saved.section_state['transform'], flatten(saved_box.transform))
        _close_values(saved.section_state['size'], saved_box.size)
        issue_id = service.create_issue('Restore section controls with review context', viewpoint=saved)
        stored = service.store.get_viewpoint(saved.id)
        assert stored == saved, 'USD serialization must retain the captured section configuration'

        changed_box = SectionBox(Gf.Matrix4d().SetTranslate(Gf.Vec3d(-7, 0, 0)), Gf.Vec3d(4, 4, 4), frozenset((Face.MAX_Y,)))
        state.edit(box=changed_box, enabled=False)
        await frames(5)
        assert not state.enabled
        assert not render.GetAttribute(ENABLED).Get()
        service.open_issue(issue_id)
        await frames(5)

        assert state.enabled is True
        assert state.box.faces == saved_box.faces
        _close_values(flatten(state.box.transform), flatten(saved_box.transform))
        _close_values(state.box.size, saved_box.size)
        assert render.GetAttribute(ENABLED).Get() is True
        restored_planes = adapter.clipping_planes(viewport)
        assert len(restored_planes) == len(saved.clipping_planes)
        for actual, expected in zip(restored_planes, saved.clipping_planes):
            _close_values(actual, expected)
        _close_values(render.GetAttribute(PLANES).Get(), [value for plane in expected_planes for value in plane])
        assert service.store.get_viewpoint(saved.id) == saved, 'Opening a review must preserve its original Section Box evidence'
        state.edit(enabled=False)
        await frames(5)
        assert not render.GetAttribute(ENABLED).Get(), 'Disabling restored Section Box controls must disable the restored clipping planes'
    finally:
        service.viewport = old_adapter
        if state is not None and previous is not None and state.stage == service.stage:
            state.apply(previous)
        if adapter is not None:
            adapter.destroy()
        if not was_enabled and manager.is_extension_enabled('section.box'):
            enable_extension('section.box', False)
        await frames(5)

async def test_unsectioned_issue_disables_later_section_controller(service):
    from issues_tag.viewport import ViewportAdapter
    manager = omni.kit.app.get_app().get_extension_manager()
    was_enabled = manager.is_extension_enabled('section.box')
    old_adapter = service.viewport
    previous = None
    if was_enabled:
        previous = importlib.import_module('section_box').get_runtime_state().snapshot
        enable_extension('section.box', False)
    adapter = None
    try:
        viewport = get_active_viewport(usd_context_name=None)
        camera = UsdGeom.Camera.Define(service.stage, '/UnsectionedReviewCamera')
        camera.AddTranslateOp().Set(Gf.Vec3d(0, 0, 20))
        viewport.camera_path = camera.GetPath()
        await frames(10)
        adapter = ViewportAdapter(service, viewport)
        service.viewport = adapter
        saved = adapter.capture()
        assert not saved.section_state, 'The fixture must capture before Section Box is enabled'
        issue_id = service.create_issue('Review captured before enabling Section Box', viewpoint=saved)
        enable_extension('section.box', True)
        from section_box.model import SectionBox, Face
        state = importlib.import_module('section_box').get_runtime_state()
        state.sync_stage()
        state.edit(box=SectionBox(Gf.Matrix4d(1), Gf.Vec3d(8, 8, 8), frozenset(Face)), enabled=True)
        await frames(5)
        assert state.enabled and adapter.clipping_planes(viewport)
        service.open_issue(issue_id)
        await frames(5)
        assert not state.enabled, 'Opening an unsectioned saved issue must disable the current Section Box controller'
        assert adapter.clipping_planes(viewport) == saved.clipping_planes, 'Current controller must not override the saved unsectioned view'
    finally:
        service.viewport = old_adapter
        if adapter:
            adapter.destroy()
        if manager.is_extension_enabled('section.box'):
            enable_extension('section.box', False)
        if was_enabled:
            enable_extension('section.box', True)
            if previous is not None:
                importlib.import_module('section_box').get_runtime_state().apply(previous)
        await frames(5)


async def test_inactive_viewport_does_not_capture_active_section_box(service):
    from issues_tag.viewport import ViewportAdapter
    from omni.kit.viewport.utility import create_viewport_window
    manager = omni.kit.app.get_app().get_extension_manager()
    was_enabled = manager.is_extension_enabled('section.box')
    window = None
    adapter = None
    state = None
    previous = None
    try:
        primary = get_active_viewport(usd_context_name=None)
        for path in ('/ActiveSectionCamera', '/InactiveSectionCamera'):
            camera = UsdGeom.Camera.Define(service.stage, path)
            camera.AddTranslateOp().Set(Gf.Vec3d(0, 0, 20))
        primary.camera_path = '/ActiveSectionCamera'
        window = create_viewport_window('Inactive issue section review', width=320, height=240, camera_path='/InactiveSectionCamera')
        assert window and window.viewport_api.stage == service.stage
        await frames(10)
        active = get_active_viewport(usd_context_name=None)
        inactive = window.viewport_api if active != window.viewport_api else primary
        assert inactive != active and inactive.stage == active.stage == service.stage
        enable_extension('section.box', True)
        from section_box.model import SectionBox, Face
        state = importlib.import_module('section_box').get_runtime_state()
        state.sync_stage()
        previous = state.snapshot
        state.edit(box=SectionBox(Gf.Matrix4d(1), Gf.Vec3d(8, 8, 8), frozenset(Face)), enabled=True)
        await frames(5)
        assert state.enabled
        active_adapter = ViewportAdapter(service, active)
        assert active_adapter.clipping_planes(active), 'Active viewport must contain the enabled Section Box cut'
        active_adapter.destroy()
        adapter = ViewportAdapter(service, inactive)
        saved = adapter.capture()
        assert not saved.section_state, 'An inactive viewport must not capture the active viewport Section Box controls'
    finally:
        if state is not None and previous is not None and state.stage == service.stage:
            state.apply(previous)
        if adapter:
            adapter.destroy()
        if not was_enabled and manager.is_extension_enabled('section.box'):
            enable_extension('section.box', False)
        if window:
            window.destroy()
        await frames(5)
