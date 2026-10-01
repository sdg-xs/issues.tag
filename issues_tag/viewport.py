"""Review camera state and surface anchors for one native viewport."""
import asyncio
from uuid import uuid4

import omni.kit.app
import omni.kit.viewport.utility as vp_util
from pxr import Gf, Sdf, Tf, Usd, UsdGeom

from .elements import make_anchor, reference_for_prim, resolve_element, world_anchor
from .model import Status, ViewpointRecord

ENABLED = 'omni:rtx:scene:sectionPlane:enabled'
PLANES = 'omni:rtx:scene:sectionPlane:plane'

PIN_COLORS = {
    Status.OPEN: (0.90, 0.25, 0.22, 1),
    Status.IN_PROGRESS: (1.0, 0.67, 0.12, 1),
    Status.RESOLVED: (0.17, 0.75, 0.46, 1),
    Status.CLOSED: (0.48, 0.55, 0.62, 1),
}
PIN_LABELS = {Status.OPEN: 'O', Status.IN_PROGRESS: 'P', Status.RESOLVED: 'R', Status.CLOSED: 'C'}
CAMERA_NAV_ATTRIBUTES = frozenset({'projection', 'focalLength', 'horizontalAperture', 'verticalAperture',
                                  'horizontalApertureOffset', 'verticalApertureOffset', 'clippingRange', 'xformOpOrder'})


def flatten(matrix):
    return tuple(float(matrix[r][c]) for r in range(4) for c in range(4))


def matrix(values):
    return Gf.Matrix4d(*values)


def pin_is_visible(stage, anchor, planes, position=None):
    position = position if position is not None else world_anchor(stage, anchor)
    if position is None:
        return False
    resolution = resolve_element(stage, anchor.element)
    prim = stage.GetPrimAtPath(resolution.prim_path)
    if UsdGeom.Imageable(prim).ComputeVisibility() == UsdGeom.Tokens.invisible:
        return False
    return all(sum(p[i] * position[i] for i in range(3)) + p[3] >= -1e-6 for p in planes)


class ViewportAdapter:
    def __init__(self, service, viewport=None, on_pin_clicked=None):
        self.service = service
        self._destroyed = False
        self._viewport = viewport
        self._placement = None
        self._registration = None
        self._items = []
        self._placement_viewport = None
        self._placement_stage = None
        self._update_sub = None
        self._scene_notice = None
        self._notice_stage = None
        self._scene_revision = 0
        self._announced_revision = 0
        self.on_pin_clicked = on_pin_clicked
        self.filtered_issue_ids = None

    @property
    def viewport(self):
        return self._viewport or vp_util.get_active_viewport()

    @property
    def scene_revision(self):
        return self._scene_revision

    def clipping_planes(self, viewport=None):
        viewport = viewport or self.viewport
        if not viewport or not viewport.stage or not viewport.render_product_path:
            return ()
        prim = viewport.stage.GetPrimAtPath(viewport.render_product_path)
        if not prim or not prim.GetAttribute(ENABLED).Get():
            return ()
        values = prim.GetAttribute(PLANES).Get() or ()
        return tuple(tuple(float(v) for v in values[i:i+4]) for i in range(0, len(values), 4))

    def evidence_overlays(self, viewport):
        item = next((item for item in self._items if item.viewport_api == viewport), None)
        if not item or not item.layer_provider:
            raise ValueError('The evidence viewport overlay layers are unavailable.')
        overlays = []
        def collect(layer):
            if 'viewport' in getattr(layer, 'categories', ()):
                return
            if hasattr(layer, 'visible'):
                overlays.append(layer)
            else:
                for child in layer.layers:
                    collect(child)
        for layer in item.layer_provider.layers:
            collect(layer)
        return tuple(overlays)

    def capture(self):
        viewport = self.viewport
        stage = self.service.stage
        if not viewport or viewport.stage != stage:
            raise ValueError('Open a viewport for this scene first.')
        camera = UsdGeom.Camera(stage.GetPrimAtPath(viewport.camera_path))
        if not camera:
            raise ValueError('The viewport camera is unavailable.')
        values = {'projection': str(camera.GetProjectionAttr().Get()),
                  'transform': list(flatten(camera.ComputeLocalToWorldTransform(Usd.TimeCode.Default()))),
                  'horizontal_aperture': float(camera.GetHorizontalApertureAttr().Get()),
                  'vertical_aperture': float(camera.GetVerticalApertureAttr().Get()),
                  'focal_length': float(camera.GetFocalLengthAttr().Get()),
                  'clipping_range': list(camera.GetClippingRangeAttr().Get())}
        visibility = tuple((str(p.GetPath()), str(UsdGeom.Imageable(p).GetVisibilityAttr().Get() or 'inherited'))
                           for p in stage.Traverse() if p.IsA(UsdGeom.Imageable) and not str(p.GetPath()).startswith(('/Issues', '/Viewport_Markups')))
        selection = tuple(reference_for_prim(stage, p) for p in self.service._context.get_selection().get_selected_prim_paths()
                          if stage.GetPrimAtPath(p))
        section = {}
        try:
            import section_box
            state = section_box.get_runtime_state()
            if state and state.stage == stage and vp_util.get_active_viewport(usd_context_name=None) == viewport:
                section = {'enabled': state.enabled, 'transform': list(flatten(state.box.transform)),
                           'size': list(state.box.size), 'faces': [f.name for f in state.box.faces]}
        except ImportError:
            pass
        return ViewpointRecord(str(uuid4()), values, self.clipping_planes(), visibility, selection,
                               section_state=section, coordinate_frame={'meters_per_unit': UsdGeom.GetStageMetersPerUnit(stage),
                                                                        'up_axis': str(UsdGeom.GetStageUpAxis(stage))})

    def restore(self, record, *, restore_camera=True):
        stage = self.service.stage
        viewport = self.viewport
        if not viewport or viewport.stage != stage:
            raise ValueError('The saved view needs a viewport in the current scene.')
        if record.coordinate_frame and (record.coordinate_frame.get('meters_per_unit') != UsdGeom.GetStageMetersPerUnit(stage) or record.coordinate_frame.get('up_axis') != str(UsdGeom.GetStageUpAxis(stage))):
            raise ValueError('This viewpoint uses a different coordinate frame; map the model before restoring it.')
        required = {'projection', 'transform', 'horizontal_aperture', 'vertical_aperture', 'focal_length', 'clipping_range'}
        if not required.issubset(record.camera):
            raise ValueError('This issue has no usable saved camera.')
        section = None
        box = None
        try:
            import section_box
            from section_box.model import SectionBox, Face
            state = section_box.get_runtime_state()
            if state and state.stage == stage and vp_util.get_active_viewport(usd_context_name=None) == viewport:
                section = state
                if record.section_state:
                    values = record.section_state
                    box = SectionBox(matrix(values['transform']), Gf.Vec3d(*values['size']), frozenset(Face[n] for n in values['faces']))
        except ImportError:
            pass
        with Usd.EditContext(stage, stage.GetSessionLayer()):
            if restore_camera:
                path = '/IssuesReviewCamera_' + str(id(viewport))
                perspective = stage.GetPrimAtPath('/OmniverseKit_Persp')
                primary = vp_util.get_active_viewport_window('Viewport')
                if (perspective and perspective.IsA(UsdGeom.Camera) and primary
                        and primary.viewport_api == viewport
                        and not any(attr.GetNumTimeSamples() for attr in perspective.GetAttributes())):
                    from omni.kit.viewport.window import get_viewport_window_instances
                    shared = any(other.viewport_api != viewport and other.viewport_api.stage == stage
                                 and str(other.viewport_api.camera_path) == '/OmniverseKit_Persp'
                                 for other in get_viewport_window_instances(None))
                    if not shared:
                        path = '/OmniverseKit_Persp'
                camera = UsdGeom.Camera.Define(stage, path)
                camera.MakeMatrixXform().Set(matrix(record.camera['transform']))
                camera.GetProjectionAttr().Set(record.camera['projection'])
                camera.GetHorizontalApertureOffsetAttr().Set(0)
                camera.GetVerticalApertureOffsetAttr().Set(0)
                for key, attr in [('horizontal_aperture', camera.GetHorizontalApertureAttr()),
                                  ('vertical_aperture', camera.GetVerticalApertureAttr()),
                                  ('focal_length', camera.GetFocalLengthAttr()), ('clipping_range', camera.GetClippingRangeAttr())]:
                    attr.Set(Gf.Vec2f(*record.camera[key]) if key == 'clipping_range' else record.camera[key])
                camera.GetPrim().CreateAttribute('omni:kit:cameraLock', Sdf.ValueTypeNames.Bool).Set(False)
            for prim_path, visible in record.visibility:
                prim = stage.GetPrimAtPath(prim_path)
                if prim and prim.IsA(UsdGeom.Imageable):
                    UsdGeom.Imageable(prim).GetVisibilityAttr().Set(visible)
            if restore_camera:
                viewport.camera_path = path
        selected = [resolve_element(stage, ref) for ref in record.selection]
        self.service._context.get_selection().set_selected_prim_paths([r.prim_path for r in selected if r.state == 'resolved'], False)
        if section:
            if box:
                section.edit(box=box, enabled=record.section_state['enabled'])
            else:
                section.edit(enabled=False)
        if not (section and box and record.section_state['enabled'] and box.faces):
            with Usd.EditContext(stage, stage.GetSessionLayer()):
                render = stage.GetPrimAtPath(viewport.render_product_path)
                if render:
                    render.CreateAttribute(ENABLED, Sdf.ValueTypeNames.Bool).Set(bool(record.clipping_planes))
                    render.CreateAttribute(PLANES, Sdf.ValueTypeNames.FloatArray).Set([v for p in record.clipping_planes for v in p] or [0,0,0,0])

    def focus(self, refs):
        paths = [resolve_element(self.service.stage, ref) for ref in refs]
        paths = [r.prim_path for r in paths if r.state == 'resolved']
        if paths:
            vp_util.frame_viewport_prims(self.viewport, paths)

    async def pick(self, screen_x, screen_y, viewport=None):
        from omni.kit.viewport.window.raycast import perform_raycast_query
        viewport = viewport or self.viewport
        stage, generation = self.service.stage, self.service.generation
        if not viewport or viewport.stage != stage:
            return None
        future = asyncio.get_running_loop().create_future()
        def complete(path, position, *args):
            if not future.done():
                future.set_result((str(path), tuple(position)))
        pixel, target = viewport.map_ndc_to_texture_pixel((screen_x, screen_y))
        if not target:
            return None
        perform_raycast_query(target, (screen_x, screen_y), pixel, complete, 'issues.surface')
        path, position = await asyncio.wait_for(future, 10)
        if self.service.stage != stage or self.service.generation != generation or not path:
            return None
        return make_anchor(stage, path, position)

    def start(self):
        if self._destroyed:
            raise ValueError('This viewport adapter has been destroyed.')
        if self._registration:
            return
        from omni.kit.viewport.registry import RegisterScene
        try:
            self._registration = RegisterScene(self._create_item, 'issues.tag.Pins')
            self._bind_scene(self.service.stage)
            self._update_sub = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(self._update, name='issues.pins')
        except Exception as startup_error:
            try:
                self.destroy()
            except Exception as cleanup_error:
                raise ExceptionGroup('Viewport startup and rollback failed', [startup_error, cleanup_error]) from None
            raise

    def _create_item(self, args):
        if self._destroyed:
            return None
        item = _ViewportItem(self, args)
        self._items.append(item)
        return item

    def _scene_changed(self, notice, stage):
        if stage != self._notice_stage:
            return
        resynced = tuple(notice.GetResyncedPaths())
        paths = tuple(notice.GetChangedInfoOnlyPaths())
        # Camera navigation changes projection, not model attachment or visibility.
        if not resynced and paths and all(
                path.IsPropertyPath() and (path.name in CAMERA_NAV_ATTRIBUTES or path.name.startswith('xformOp:'))
                and (prim := stage.GetPrimAtPath(path.GetPrimPath())) and prim.IsA(UsdGeom.Camera)
                and not prim.GetChildren() and not prim.IsInstance() for path in paths):
            return
        self._scene_revision += 1

    def _bind_scene(self, stage):
        if self._scene_notice:
            self._scene_notice.Revoke()
        self._notice_stage = stage
        self._scene_notice = Tf.Notice.Register(Usd.Notice.ObjectsChanged, self._scene_changed, stage) if stage else None
        self._scene_revision += 1

    def _update(self, event):
        if self._destroyed:
            return
        if self.service.stage != self._notice_stage:
            self._bind_scene(self.service.stage)
        if self._placement and not self._placement.done() and self.service.stage != self._placement_stage:
            self.cancel_placement()
        for item in tuple(self._items):
            item.sync()
        if self._announced_revision != self._scene_revision:
            self._announced_revision = self._scene_revision
            self.service._notify()

    def _pin_clicked(self, issue_id):
        if self.on_pin_clicked:
            self.on_pin_clicked(issue_id)
        else:
            self.service.open_issue(issue_id)

    def begin_placement(self):
        viewport = self.viewport
        if not viewport or viewport.stage != self.service.stage:
            raise ValueError('Open a viewport for this scene first.')
        if self._placement and not self._placement.done():
            self._placement.cancel()
        self._placement = asyncio.get_running_loop().create_future()
        self._placement_viewport = viewport
        self._placement_stage = self.service.stage
        self._placement.add_done_callback(self._placement_finished)
        self.service._notify()
        return self._placement

    @property
    def is_placing(self):
        return self._placement is not None and not self._placement.done()

    def cancel_placement(self):
        if self.is_placing:
            self._placement.cancel()
            self.service._notify()

    def _placement_finished(self, pending):
        if pending is self._placement:
            self.service._notify()

    async def request_placement(self):
        stage, generation = self.service.stage, self.service.generation
        anchor = await self.begin_placement()
        if self.service.stage != stage or self.service.generation != generation:
            return None
        return anchor

    async def _place_at(self, viewport, mouse, placement=None):
        pending = placement if placement is not None else self._placement
        if not pending or pending is not self._placement or pending.done() or viewport != self._placement_viewport:
            return
        try:
            anchor = await self.pick(*mouse, viewport=viewport)
        except Exception as error:
            if not pending.done():
                pending.set_exception(error)
            return
        if pending is self._placement and not pending.done() and anchor:
            pending.set_result(anchor)

    def destroy(self):
        if self._destroyed:
            return
        self._destroyed = True
        registration, self._registration = self._registration, None
        notice, self._scene_notice = self._scene_notice, None
        pending, self._placement = self._placement, None
        items, self._items = tuple(self._items), []
        self._update_sub = None
        self._notice_stage = None
        self._placement_viewport = None
        self._placement_stage = None
        self.on_pin_clicked = None
        failures = []
        def clean(operation):
            try:
                operation()
            except Exception as error:
                failures.append(error)
        # Unregister first: registry callbacks can reenter item destruction.
        if registration:
            clean(registration.destroy)
        for item in items:
            clean(item.destroy)
        if notice:
            clean(notice.Revoke)
        if pending and not pending.done():
            clean(pending.cancel)
        if failures:
            raise ExceptionGroup('Viewport cleanup failed', failures)

class _PlacementClick:
    """Build a native scene gesture without requiring a global input hook."""
    @staticmethod
    def gesture(adapter, viewport):
        from omni.ui import scene as sc
        placement = adapter._placement
        class Click(sc.ClickGesture):
            def on_ended(self):
                if self.state != sc.GestureState.CANCELED:
                    mouse = self.sender.gesture_payload.mouse
                    asyncio.ensure_future(adapter._place_at(viewport, tuple(mouse), placement))
        return Click(mouse_button=0)


class _PinManipulator:
    @staticmethod
    def create(adapter, viewport, item):
        import omni.ui as ui
        from omni.ui import scene as sc
        class Manipulator(sc.Manipulator):
            def on_build(self):
                self._objects = []
                if viewport.stage != adapter.service.stage:
                    return
                if adapter._placement and not adapter._placement.done() and adapter._placement_viewport == viewport:
                    self._objects.append(sc.Screen(gesture=_PlacementClick.gesture(adapter, viewport)))
                for issue_id, position, status in item.pins:
                    with sc.Transform(transform=sc.Matrix44.get_translation_matrix(*position)):
                        with sc.Transform(look_at=sc.Transform.LookAt.CAMERA, scale_to=sc.Space.SCREEN):
                            self._objects.append(sc.Rectangle(24, 24, color=ui.color(*PIN_COLORS[status]),
                                gestures=[sc.ClickGesture(on_ended_fn=lambda sender, issue_id=issue_id: adapter._pin_clicked(issue_id))]))
                            self._objects.append(sc.Label(PIN_LABELS[status], alignment=ui.Alignment.CENTER,
                                                          color=ui.color.white, size=12))
        return Manipulator()


class _ViewportItem:
    categories = ('manipulator',)
    name = 'Issues'
    visible = True

    def __init__(self, adapter, args):
        self.adapter = adapter
        self.viewport_api = args['viewport_api']
        self.layer_provider = args.get('layer_provider')
        self.visible_issue_ids = ()
        self.pins = ()
        self._signature = None
        self._computed = None
        self.manipulator = _PinManipulator.create(adapter, self.viewport_api, self)

    def sync(self):
        stage = self.viewport_api.stage
        planes = self.adapter.clipping_planes(self.viewport_api)
        computed = (stage, self.adapter.service.stage, self.adapter._scene_revision, planes, self.adapter.filtered_issue_ids)
        if computed != self._computed:
            pins = []
            if stage and stage == self.adapter.service.stage:
                for issue in self.adapter.service.list_issues():
                    if self.adapter.filtered_issue_ids is not None and issue.id not in self.adapter.filtered_issue_ids:
                        continue
                    if not issue.anchor:
                        continue
                    position = world_anchor(stage, issue.anchor)
                    if position is not None and pin_is_visible(stage, issue.anchor, planes, position):
                        pins.append((issue.id, position, issue.status))
            self.pins = tuple(pins)
            self._computed = computed
        armed = bool(self.adapter._placement and not self.adapter._placement.done() and self.adapter._placement_viewport == self.viewport_api)
        placement = self.adapter._placement if armed else None
        signature = (stage, self.pins, placement)
        self.visible_issue_ids = tuple(issue_id for issue_id, _, _ in self.pins)
        if signature != self._signature:
            self._signature = signature
            self.manipulator.invalidate()

    def destroy(self):
        self.pins = ()
        self.layer_provider = None
        self.visible_issue_ids = ()
        manipulator, self.manipulator = self.manipulator, None
        if self in self.adapter._items:
            self.adapter._items.remove(self)
        if manipulator:
            manipulator.destroy()
