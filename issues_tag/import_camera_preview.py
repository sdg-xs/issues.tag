"""Temporary viewport camera for reviewing an import without recalling evidence state."""
from uuid import uuid4

from pxr import Gf, Sdf, Usd, UsdGeom


def _copy_exposure(source, destination):
    if not source:
        return
    applied = source.GetMetadata('apiSchemas')
    if applied:
        schemas = [name for name in applied.ApplyOperations([])
                   if name.startswith(('OmniRtxCameraExposureAPI_', 'OmniRtxCameraAutoExposureAPI_'))]
        if schemas:
            destination.SetMetadata('apiSchemas', Sdf.TokenListOp.CreateExplicit(schemas))
    for attribute in source.GetAttributes():
        if attribute.HasAuthoredValueOpinion() and attribute.GetName().startswith(('exposure:', 'omni:rtx:autoExposure:')):
            destination.CreateAttribute(attribute.GetName(), attribute.GetTypeName(), attribute.IsCustom()).Set(attribute.Get())


class ImportCameraPreview:
    def __init__(self, viewport, stage):
        self.viewport = viewport
        self.stage = stage
        self._path = None
        self._previous_camera = None
        self._relationship_path = None
        self._relationship_backup = None
        self._created_specs = []

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
        session = self.stage.GetSessionLayer()
        try:
            with Usd.EditContext(self.stage, session):
                camera = UsdGeom.Camera.Define(self.stage, path)
                camera.MakeMatrixXform().Set(Gf.Matrix4d(*values['transform']))
                camera.GetProjectionAttr().Set(values['projection'])
                camera.GetHorizontalApertureAttr().Set(values['horizontal_aperture'])
                camera.GetVerticalApertureAttr().Set(values['vertical_aperture'])
                camera.GetFocalLengthAttr().Set(values['focal_length'])
                camera.GetClippingRangeAttr().Set(Gf.Vec2f(*values['clipping_range']))
                camera.GetPrim().CreateAttribute('omni:kit:cameraLock', Sdf.ValueTypeNames.Bool).Set(False)
                _copy_exposure(self.stage.GetPrimAtPath(self._previous_camera), camera.GetPrim())
                product_path = getattr(self.viewport, 'render_product_path', None)
                if product_path:
                    product = self.stage.GetPrimAtPath(product_path)
                    if not product:
                        raise ValueError('The viewport render product is unavailable.')
                    self._relationship_path = Sdf.Path(product_path).AppendProperty('camera')
                    self._created_specs = [prefix for prefix in Sdf.Path(product_path).GetPrefixes()
                                           if not session.GetPrimAtPath(prefix)]
                    if session.GetRelationshipAtPath(self._relationship_path):
                        self._relationship_backup = Sdf.Layer.CreateAnonymous()
                        Sdf.CreatePrimInLayer(self._relationship_backup, product_path)
                        Sdf.CopySpec(session, self._relationship_path, self._relationship_backup, self._relationship_path)
                    product.CreateRelationship('camera').SetTargets([path])
                self.viewport.camera_path = path
        except Exception:
            self.close()
            raise

    def close(self):
        path, self._path = self._path, None
        previous, self._previous_camera = self._previous_camera, None
        relationship, self._relationship_path = self._relationship_path, None
        backup, self._relationship_backup = self._relationship_backup, None
        created, self._created_specs = self._created_specs, []
        if path is None:
            return
        session = self.stage.GetSessionLayer()
        same_stage = self.viewport.stage == self.stage
        current = str(self.viewport.camera_path) if same_stage else None
        owns_product = relationship is None or (same_stage and str(self.viewport.render_product_path) == str(relationship.GetPrimPath()))
        relation_spec = session.GetRelationshipAtPath(relationship) if relationship else None
        owns_relation = relation_spec is not None and relation_spec.GetInfo('targetPaths') == Sdf.PathListOp.CreateExplicit([Sdf.Path(path)])
        try:
            with Usd.EditContext(self.stage, session):
                if same_stage and owns_product and current == path and previous and self.stage.GetPrimAtPath(previous):
                    self.viewport.camera_path = previous
        finally:
            with Usd.EditContext(self.stage, session):
                if owns_relation:
                    if backup:
                        Sdf.CopySpec(backup, relationship, session, relationship)
                        if same_stage and owns_product and current != path and self.stage.GetPrimAtPath(current):
                            self.stage.GetRelationshipAtPath(relationship).SetTargets([current])
                    else:
                        self.stage.GetPrimAtPath(relationship.GetPrimPath()).RemoveProperty('camera')
                self.stage.RemovePrim(path)
                for prim_path in reversed(created):
                    spec = session.GetPrimAtPath(prim_path)
                    if spec and not spec.properties and not spec.nameChildren and set(spec.ListInfoKeys()) == {'specifier'}:
                        self.stage.RemovePrim(prim_path)
