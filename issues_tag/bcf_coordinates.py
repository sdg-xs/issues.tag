"""Map standard BCF world coordinates through a composed USD reference."""
import math
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class ViewpointImportOptions:
    reference_path: str | None = None
    coordinate_mode: str = 'source_world'
    fov_mode: str = 'file'

    def __post_init__(self):
        if self.coordinate_mode not in ('source_world', 'reference_local'):
            raise ValueError('Unknown BCF coordinate mode.')
        if self.fov_mode not in ('file', 'horizontal'):
            raise ValueError('Unknown BCF FOV mode.')
        if self.reference_path is not None and (not isinstance(self.reference_path, str) or not self.reference_path.startswith('/')):
            raise ValueError('Invalid BCF reference path.')


class ReferenceSelectionRequired(ValueError):
    def __init__(self, paths):
        self.paths = tuple(paths)
        super().__init__('BCF coordinate mapping found multiple IFCSITE Xforms: '
                         + ', '.join(self.paths) + '. Select the reference site.')


def stage_mapping(stage, *, reference_path=None, coordinate_mode='source_world'):
    ViewpointImportOptions(reference_path=reference_path, coordinate_mode=coordinate_mode)
    from pxr import Gf, Usd, UsdGeom
    local_layers = set(stage.GetLayerStack())
    roots = []
    sites = []
    for prim in stage.Traverse():
        if any(prim.GetPath().HasPrefix(path) for path in ('/Issues', '/Viewport_Markups')):
            continue
        site_type = prim.GetAttribute('omni:hoops:metadata:TYPE')
        if prim.IsA(UsdGeom.Xform) and site_type and site_type.Get() == 'IFCSITE':
            sites.append(prim)
        foreign = [s for s in prim.GetPrimStack() if s.layer not in local_layers]
        if not foreign:
            continue
        parent_foreign = any(s.layer not in local_layers for s in prim.GetParent().GetPrimStack())
        if not parent_foreign:
            roots.append(prim)
    if reference_path is not None:
        sites = [prim for prim in sites if str(prim.GetPath()) == reference_path]
        if not sites:
            raise ValueError('The selected reference is no longer an IFCSITE Xform. Import the file again.')
    elif len(sites) > 1:
        raise ReferenceSelectionRequired(sorted(str(prim.GetPath()) for prim in sites))
    if not sites and len(roots) > 1:
        raise ValueError('BCF coordinate mapping needs one model reference; multiple instances are ambiguous.')
    target_units = UsdGeom.GetStageMetersPerUnit(stage)
    target_axis = str(UsdGeom.GetStageUpAxis(stage))
    if not math.isfinite(target_units) or target_units <= 0 or target_axis not in ('Y', 'Z'):
        raise ValueError('Invalid USD target coordinate frame.')
    delta = Gf.Matrix4d(1)
    source_units, source_axis, anchor = target_units, target_axis, ''
    prim = sites[0] if sites else None
    if prim is None and roots:
        root = roots[0]
        defaults = [p for p in Usd.PrimRange(root) if p.GetName() == 'Default' and p.IsA(UsdGeom.Xformable)]
        defaults = [p for p in defaults if not any(p.GetPath().HasPrefix(other.GetPath()) for other in defaults if other != p)]
        if len(defaults) > 1:
            raise ValueError('BCF coordinate mapping found multiple Default frames; select one model instance.')
        prim = defaults[0] if defaults else root
    if prim is not None:
        anchor = str(prim.GetPath())
        spec = next((s for s in prim.GetPrimStack() if s.layer not in local_layers), None)
    else:
        spec = None
    if spec is not None:
        source = Usd.Stage.Open(spec.layer)
        source_prim = source.GetPrimAtPath(spec.path)
        if not source_prim:
            raise ValueError('Cannot resolve the original USD reference frame.')
        cache = UsdGeom.XformCache()
        original = cache.GetLocalToWorldTransform(source_prim)
        if abs(original.GetDeterminant()) < 1e-12:
            raise ValueError('The source reference frame is singular.')
        delta = original.GetInverse() * cache.GetLocalToWorldTransform(prim)
        source_units = UsdGeom.GetStageMetersPerUnit(source)
        source_axis = str(UsdGeom.GetStageUpAxis(source))
    if coordinate_mode == 'reference_local':
        if prim is None:
            raise ValueError('Reference-local BCF coordinates require a model reference frame.')
        delta = UsdGeom.XformCache().GetLocalToWorldTransform(prim)
    basis = Gf.Matrix4d(1)
    if source_axis == 'Y':
        basis = Gf.Matrix4d(1,0,0,0, 0,0,-1,0, 0,1,0,0, 0,0,0,1)
    elif source_axis != 'Z':
        raise ValueError('Unsupported USD source up axis.')
    if not math.isfinite(source_units) or source_units <= 0:
        raise ValueError('Invalid USD source units.')
    basis = basis * Gf.Matrix4d().SetScale(1 / source_units)
    matrix = basis * delta
    # Camera projection and plane distances require a rigid, uniformly scaled frame.
    uniform_scale(matrix)
    values = tuple(float(v) for row in matrix for v in row)
    return values, float(target_units), target_axis, anchor


def uniform_scale(matrix):
    from pxr import Gf
    if any(not math.isfinite(float(v)) for row in matrix for v in row) or any(abs(matrix[i][3]) > 1e-9 for i in range(3)) or abs(matrix[3][3]-1) > 1e-9:
        raise ValueError('Invalid BCF reference matrix.')
    rows = [Gf.Vec3d(*tuple(matrix[i])[:3]) for i in range(3)]
    lengths = [r.GetLength() for r in rows]
    scale = sum(lengths) / 3
    if scale <= 0 or matrix.GetDeterminant() <= 0 or any(abs(v-scale) > scale*1e-6 for v in lengths) or any(abs(Gf.Dot(rows[i], rows[j])) > scale*scale*1e-6 for i,j in ((0,1),(0,2),(1,2))):
        raise ValueError('BCF camera mapping requires uniform scale without shear or reflection.')
    return scale


def transform_view(view, values, units, axis, *, inverse=False):
    from pxr import Gf
    if not isinstance(values, (list, tuple)) or len(values) != 16 or any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in values):
        raise ValueError('Invalid BCF reference matrix.')
    matrix = Gf.Matrix4d(*values)
    uniform_scale(matrix)
    if inverse:
        matrix = matrix.GetInverse()
    scale = uniform_scale(matrix)
    camera = dict(view.camera)
    if camera:
        pose = Gf.Matrix4d(*camera['transform'])
        transformed = pose * matrix
        for i in range(3):
            row = transformed.GetRow(i)
            transformed.SetRow(i, Gf.Vec4d(row[0]/scale, row[1]/scale, row[2]/scale, 0))
        camera['transform'] = [float(v) for row in transformed for v in row]
        for key in ('horizontal_aperture', 'vertical_aperture', 'focal_length'):
            camera[key] *= scale
        camera['clipping_range'] = [v*scale for v in camera['clipping_range']]
    clips = []
    for plane in view.clipping_planes:
        normal = Gf.Vec3d(*plane[:3])
        length_sq = Gf.Dot(normal, normal)
        if length_sq == 0:
            raise ValueError('Invalid BCF clipping plane normal.')
        location = normal * (-plane[3] / length_sq)
        location = matrix.Transform(location)
        normal = matrix.TransformDir(normal).GetNormalized()
        clips.append((*tuple(normal), -Gf.Dot(normal, location)))
    frame = dict(view.coordinate_frame, meters_per_unit=units, up_axis=axis)
    return replace(view, camera=camera, clipping_planes=tuple(clips), coordinate_frame=frame)


def source_view(view):
    """Rebuild the standard projection and pose from retained archive values."""
    original = export_view(view)
    source = view.coordinate_frame.get('bcf_source_camera')
    if not source:
        return original
    from .bcf import _cross, _normalize
    direction = _normalize(source['direction'])
    right = _normalize(_cross(direction, source['up']))
    up = _cross(right, direction)
    perspective = source['field_of_view'] is not None
    vertical = 24.0 if perspective else source['view_to_world_scale'] * 10
    focal = vertical / (2 * math.tan(math.radians(source['field_of_view']) / 2)) if perspective else 50
    camera = dict(original.camera, projection='perspective' if perspective else 'orthographic',
                  transform=[*right, 0, *up, 0, *(-v for v in direction), 0, *source['position'], 1],
                  horizontal_aperture=vertical * source['aspect_ratio'], vertical_aperture=vertical,
                  focal_length=focal, clipping_range=[.01, 1000000])
    frame = {key: value for key, value in original.coordinate_frame.items()
             if key not in ('bcf_reference_mapping', 'bcf_reference_prim', 'bcf_coordinate_mode', 'bcf_fov_mode', 'bcf_source_clipping_planes')}
    clips = view.coordinate_frame.get('bcf_source_clipping_planes', original.clipping_planes)
    return replace(original, camera=camera, coordinate_frame=frame, clipping_planes=tuple(tuple(plane) for plane in clips))


def import_view(view, mapping, *, options=None):
    # Native Omniverse records already carry their USD world frame.
    if not view.camera or 'bcf_has_visibility' not in view.coordinate_frame or options is None and 'bcf_reference_mapping' in view.coordinate_frame:
        return view
    if options is not None:
        view = source_view(view)
        if options.fov_mode == 'horizontal':
            source = view.coordinate_frame.get('bcf_source_camera', {})
            if source.get('version') != '2.1' or view.camera.get('projection') != 'perspective':
                raise ValueError('BCF horizontal FOV requires a standard 2.1 perspective camera.')
            camera = dict(view.camera)
            camera['focal_length'] = camera['horizontal_aperture'] / (2 * math.tan(math.radians(source['field_of_view']) / 2))
            view = replace(view, camera=camera)
    values, units, axis, anchor = mapping
    converted = transform_view(view, values, units, axis)
    frame = dict(converted.coordinate_frame, bcf_reference_mapping=list(values), bcf_reference_prim=anchor)
    if options is not None:
        frame.update(bcf_coordinate_mode=options.coordinate_mode, bcf_fov_mode=options.fov_mode)
        frame['bcf_source_clipping_planes'] = [list(plane) for plane in view.clipping_planes]
    return replace(converted, coordinate_frame=frame)


def export_view(view):
    values = view.coordinate_frame.get('bcf_reference_mapping')
    return transform_view(view, values, 1, 'Z', inverse=True) if values else view
