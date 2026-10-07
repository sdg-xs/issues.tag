"""Temporary viewport camera for reviewing an import without recalling evidence state."""
from uuid import uuid4

from pxr import Gf, Sdf, Usd, UsdGeom


class ImportCameraPreview:
    def __init__(self, viewport, stage):
        self.viewport = viewport
        self.stage = stage
        self._path = None
        self._previous_camera = None

    def show(self, viewpoint):
        if not self.viewport or self.viewport.stage != self.stage:
            raise ValueError('Open a viewport for this scene first.')
        values = viewpoint.camera
        required = {'projection', 'transform', 'horizontal_aperture', 'vertical_aperture', 'focal_length', 'clipping_range'}
        if not required.issubset(values):
            raise ValueError('This viewpoint has no usable camera.')
        self.close()
        path = '/IssuesImportPreview_' + uuid4().hex
        while self.stage.GetPrimAtPath(path):
            path = '/IssuesImportPreview_' + uuid4().hex
        self._path = path
        self._previous_camera = str(self.viewport.camera_path)
        try:
            with Usd.EditContext(self.stage, self.stage.GetSessionLayer()):
                camera = UsdGeom.Camera.Define(self.stage, path)
                camera.MakeMatrixXform().Set(Gf.Matrix4d(*values['transform']))
                camera.GetProjectionAttr().Set(values['projection'])
                camera.GetHorizontalApertureAttr().Set(values['horizontal_aperture'])
                camera.GetVerticalApertureAttr().Set(values['vertical_aperture'])
                camera.GetFocalLengthAttr().Set(values['focal_length'])
                camera.GetClippingRangeAttr().Set(Gf.Vec2f(*values['clipping_range']))
                camera.GetPrim().CreateAttribute('omni:kit:cameraLock', Sdf.ValueTypeNames.Bool).Set(False)
            self.viewport.camera_path = path
        except Exception:
            self.close()
            raise

    def close(self):
        path, self._path = self._path, None
        previous, self._previous_camera = self._previous_camera, None
        if path is None:
            return
        try:
            if (self.viewport.stage == self.stage and str(self.viewport.camera_path) == path
                    and previous and self.stage.GetPrimAtPath(previous)):
                self.viewport.camera_path = previous
        finally:
            with Usd.EditContext(self.stage, self.stage.GetSessionLayer()):
                self.stage.RemovePrim(path)
