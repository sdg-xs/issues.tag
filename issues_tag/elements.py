"""Match source identities within a reference instance, never by proximity."""
from dataclasses import dataclass
import hashlib
import math

from pxr import Gf, Sdf, Usd, UsdGeom

from .model import Anchor, ElementRef

SOURCE_FIELDS = (
    "ifc:GlobalId", "IFC:GlobalId", "GlobalId", "revit:UniqueId", "Revit:UniqueId",
)


@dataclass(frozen=True)
class Resolution:
    state: str
    prim_path: str = ""


def reference_for_prim(stage, path):
    prim = stage.GetPrimAtPath(path)
    if not prim or not prim.IsActive():
        raise ValueError("Select a loaded model element.")
    instance_path, model_id = "", ""
    parent = prim
    while parent and not parent.IsPseudoRoot():
        refs = parent.GetMetadata("references")
        if refs:
            items = refs.GetAddedOrExplicitItems()
            if items:
                instance_path = str(parent.GetPath())
                model_id = Sdf.ComputeAssetPathRelativeToLayer(stage.GetRootLayer(), items[0].assetPath)
                break
        parent = parent.GetParent()
    if not instance_path:
        instance_path = "/" + str(prim.GetPath()).strip("/").split("/")[0]
    for field in SOURCE_FIELDS:
        attr = prim.GetAttribute(field)
        if attr and attr.Get():
            return ElementRef(model_id, instance_path, str(attr.Get()), field, str(prim.GetPath()))
    return ElementRef(model_id, instance_path, str(prim.GetPath()), "path", str(prim.GetPath()))


def resolve_element(stage, reference):
    if not stage:
        return Resolution("missing")
    if reference.model_id:
        scope = stage.GetPrimAtPath(reference.instance_path)
        if not scope or reference_for_prim(stage, scope.GetPath()).model_id != reference.model_id:
            return Resolution("missing")
    if reference.id_kind == "path":
        prim = stage.GetPrimAtPath(reference.prim_path or reference.source_id)
        return Resolution("resolved", str(prim.GetPath())) if prim and prim.IsActive() else Resolution("missing")
    scope = stage.GetPrimAtPath(reference.instance_path) if reference.instance_path else stage.GetPseudoRoot()
    if not scope or not scope.IsActive():
        return Resolution("missing")
    fields = SOURCE_FIELDS if reference.id_kind in ("ifc", "authoring_tool_id") else (reference.id_kind,)
    matches = []
    for prim in Usd.PrimRange(scope):
        if not prim.IsActive():
            continue
        if any(prim.GetAttribute(field) and str(prim.GetAttribute(field).Get()) == reference.source_id for field in fields):
            matches.append(str(prim.GetPath()))
    if len(matches) == 1:
        return Resolution("resolved", matches[0])
    return Resolution("ambiguous" if matches else "missing")


def geometry_digest(prim):
    values = [prim.GetTypeName()]
    for name in ("points", "faceVertexCounts", "faceVertexIndices", "size", "radius", "height", "extent"):
        attr = prim.GetAttribute(name)
        if attr:
            values.append((name, repr(attr.Get())))
    return hashlib.sha256(repr(values).encode("utf-8")).hexdigest()


def make_anchor(stage, path, world_position):
    if len(world_position) != 3 or not all(math.isfinite(float(v)) for v in world_position):
        raise ValueError("The picked surface position is invalid.")
    reference = reference_for_prim(stage, path)
    prim = stage.GetPrimAtPath(path)
    transform = UsdGeom.XformCache().GetLocalToWorldTransform(prim)
    if abs(transform.GetDeterminant()) < 1e-12:
        raise ValueError("The element has a singular transform and cannot hold a reliable pin.")
    local = transform.GetInverse().Transform(Gf.Vec3d(*world_position))
    return Anchor(reference, tuple(local), geometry_digest(prim))


def attachment_state(stage, anchor):
    if anchor is None:
        return "missing"
    resolution = resolve_element(stage, anchor.element)
    if resolution.state != "resolved":
        return resolution.state
    digest = geometry_digest(stage.GetPrimAtPath(resolution.prim_path))
    if anchor.confidence != "verified" or not anchor.geometry_digest or digest != anchor.geometry_digest:
        return "needs_review"
    return "verified"


def world_anchor(stage, anchor):
    if anchor is None or attachment_state(stage, anchor) != "verified":
        return None
    result = resolve_element(stage, anchor.element)
    transform = UsdGeom.XformCache().GetLocalToWorldTransform(stage.GetPrimAtPath(result.prim_path))
    return tuple(transform.Transform(Gf.Vec3d(*anchor.local_position)))
