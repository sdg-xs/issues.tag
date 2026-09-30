"""Review camera state and surface anchors for one native viewport."""
import asyncio
from uuid import uuid4

import omni.kit.app
import omni.kit.viewport.utility as vp_util
from pxr import Gf, Sdf, Usd, UsdGeom

from .elements import make_anchor, reference_for_prim, resolve_element, world_anchor
from .model import ViewpointRecord

ENABLED = 'omni:rtx:scene:sectionPlane:enabled'
PLANES = 'omni:rtx:scene:sectionPlane:plane'


def flatten(matrix):
    return tuple(float(matrix[r][c]) for r in range(4) for c in range(4))


def matrix(values):
    return Gf.Matrix4d(*values)


def pin_is_visible(stage, anchor, planes):
    position = world_anchor(stage, anchor)
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
        self._viewport = viewport
        self._placement = None
        self._registration = None
        self._items = []
        self._placement_viewport = None
        self._placement_stage = None
        self._update_sub = None
        self.on_pin_clicked = on_pin_clicked

    @property
    def viewport(self):
        return self._viewport or vp_util.get_active_viewport()

    def clipping_planes(self, viewport=None):
        viewport = viewport or self.viewport
        if not viewport or not viewport.stage:
            return ()
        prim = viewport.stage.GetPrimAtPath(viewport.render_product_path)
        if not prim or not prim.GetAttribute(ENABLED).Get():
            return ()
        values = prim.GetAttribute(PLANES).Get() or ()
        return tuple(tuple(float(v) for v in values[i:i+4]) for i in range(0, len(values), 4))

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
            if state and state.stage == stage:
                section = {'enabled': state.enabled, 'transform': list(flatten(state.box.transform)),
                           'size': list(state.box.size), 'faces': [f.name for f in state.box.faces]}
        except ImportError:
            pass
        return ViewpointRecord(str(uuid4()), values, self.clipping_planes(), visibility, selection,
                               section_state=section, coordinate_frame={'meters_per_unit': UsdGeom.GetStageMetersPerUnit(stage),
                                                                        'up_axis': str(UsdGeom.GetStageUpAxis(stage))})

    def restore(self, record):
        stage = self.service.stage
        viewport = self.viewport
        if not viewport or viewport.stage != stage:
            raise ValueError('The saved view needs a viewport in the current scene.')
        if record.coordinate_frame and (record.coordinate_frame.get('meters_per_unit') != UsdGeom.GetStageMetersPerUnit(stage) or record.coordinate_frame.get('up_axis') != str(UsdGeom.GetStageUpAxis(stage))):
            raise ValueError('This viewpoint uses a different coordinate frame; map the model before restoring it.')
        required = {'projection', 'transform', 'horizontal_aperture', 'vertical_aperture', 'focal_length', 'clipping_range'}
        if not required.issubset(record.camera):
            raise ValueError('This issue has no usable saved camera.')
        path = '/IssuesReviewCamera_' + str(id(viewport))
        with Usd.EditContext(stage, stage.GetSessionLayer()):
            camera = UsdGeom.Camera.Define(stage, path)
            camera.MakeMatrixXform().Set(matrix(record.camera['transform']))
            camera.GetProjectionAttr().Set(record.camera['projection'])
            for key, attr in [('horizontal_aperture', camera.GetHorizontalApertureAttr()),
                              ('vertical_aperture', camera.GetVerticalApertureAttr()),
                              ('focal_length', camera.GetFocalLengthAttr()), ('clipping_range', camera.GetClippingRangeAttr())]:
                attr.Set(Gf.Vec2f(*record.camera[key]) if key == 'clipping_range' else record.camera[key])
            for prim_path, visible in record.visibility:
                prim = stage.GetPrimAtPath(prim_path)
                if prim and prim.IsA(UsdGeom.Imageable):
                    UsdGeom.Imageable(prim).GetVisibilityAttr().Set(visible)
            render = stage.GetPrimAtPath(viewport.render_product_path)
            if render:
                render.CreateAttribute(ENABLED, Sdf.ValueTypeNames.Bool).Set(bool(record.clipping_planes))
                render.CreateAttribute(PLANES, Sdf.ValueTypeNames.FloatArray).Set([v for p in record.clipping_planes for v in p] or [0,0,0,0])
        viewport.camera_path = path
        selected = [resolve_element(stage, ref) for ref in record.selection]
        self.service._context.get_selection().set_selected_prim_paths([r.prim_path for r in selected if r.state == 'resolved'], False)
        if record.section_state:
            try:
                import section_box
                from section_box.model import SectionBox, Face
                state = section_box.get_runtime_state()
                if state and state.stage == stage:
                    values = record.section_state
                    state.edit(box=SectionBox(matrix(values['transform']), Gf.Vec3d(*values['size']), frozenset(Face[n] for n in values['faces'])), enabled=values['enabled'])
            except ImportError:
                pass

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
        if self._registration:
            return
        from omni.kit.viewport.registry import RegisterScene
        self._registration = RegisterScene(self._create_item, 'issues.tag.Pins')
        self._update_sub = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(self._update, name='issues.pins')

    def _create_item(self, args):
        item = _ViewportItem(self, args)
        self._items.append(item)
        return item

    def _update(self, event):
        if self._placement and not self._placement.done() and self.service.stage != self._placement_stage:
            self._placement.cancel()
        for item in tuple(self._items):
            item.sync()

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
        return self._placement

    async def request_placement(self):
        return await self.begin_placement()

    async def _place_at(self, viewport, mouse):
        pending = self._placement
        if not pending or pending.done() or viewport != self._placement_viewport:
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
        self._update_sub = None
        if self._placement and not self._placement.done():
            self._placement.cancel()
        self._placement = None
        if self._registration:
            self._registration.destroy()
        self._registration = None
        for item in tuple(self._items):
            item.destroy()
        self._items.clear()

class _PlacementClick:
    """Build a native scene gesture without requiring a global input hook."""
    @staticmethod
    def gesture(adapter, viewport):
        from omni.ui import scene as sc
        class Click(sc.ClickGesture):
            def on_ended(self):
                if self.state != sc.GestureState.CANCELED:
                    mouse = self.sender.gesture_payload.mouse
                    asyncio.ensure_future(adapter._place_at(viewport, mouse))
        return Click(mouse_button=0)


class _PinManipulator:
    @staticmethod
    def create(adapter, viewport):
        import omni.ui as ui
        from omni.ui import scene as sc
        class Manipulator(sc.Manipulator):
            def on_build(self):
                self._objects = []
                if viewport.stage != adapter.service.stage:
                    return
                if adapter._placement and not adapter._placement.done() and adapter._placement_viewport == viewport:
                    self._objects.append(sc.Screen(gesture=_PlacementClick.gesture(adapter, viewport)))
                for issue in adapter.service.list_issues():
                    if not issue.anchor or not pin_is_visible(viewport.stage, issue.anchor, adapter.clipping_planes(viewport)):
                        continue
                    position = world_anchor(viewport.stage, issue.anchor)
                    with sc.Transform(transform=sc.Matrix44.get_translation_matrix(*position)):
                        with sc.Transform(look_at=sc.Transform.LookAt.CAMERA, scale_to=sc.Space.SCREEN):
                            self._objects.append(sc.Rectangle(18, 18, color=ui.color(0.17, 0.88, 0.76, 1),
                                gestures=[sc.ClickGesture(on_ended_fn=lambda sender, issue_id=issue.id: adapter._pin_clicked(issue_id))]))
        return Manipulator()


class _ViewportItem:
    categories = ('manipulator',)
    name = 'Issues'
    visible = True

    def __init__(self, adapter, args):
        self.adapter = adapter
        self.viewport_api = args['viewport_api']
        self.visible_issue_ids = ()
        self._signature = None
        self.manipulator = _PinManipulator.create(adapter, self.viewport_api)

    def sync(self):
        stage = self.viewport_api.stage
        eligible = ()
        if stage and stage == self.adapter.service.stage:
            planes = self.adapter.clipping_planes(self.viewport_api)
            eligible = tuple((issue.id, world_anchor(stage, issue.anchor)) for issue in self.adapter.service.list_issues()
                             if issue.anchor and pin_is_visible(stage, issue.anchor, planes))
        armed = bool(self.adapter._placement and not self.adapter._placement.done() and self.adapter._placement_viewport == self.viewport_api)
        signature = (stage, eligible, armed)
        self.visible_issue_ids = tuple(issue_id for issue_id, _ in eligible)
        if signature != self._signature:
            self._signature = signature
            self.manipulator.invalidate()

    def destroy(self):
        if self.manipulator:
            self.manipulator.destroy()
            self.manipulator = None
        if self in self.adapter._items:
            self.adapter._items.remove(self)
