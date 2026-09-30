from pathlib import Path
from pxr import Gf, Sdf, Usd, UsdGeom
from verify_kit import ROOT


def two_buildings(stage):
    path = ROOT / "verification" / "anchor_building.usda"
    source = Usd.Stage.CreateInMemory()
    root = UsdGeom.Xform.Define(source, "/Model")
    cube = UsdGeom.Cube.Define(source, "/Model/Cube")
    cube.GetSizeAttr().Set(2)
    cube.GetPrim().CreateAttribute("ifc:GlobalId", Sdf.ValueTypeNames.String).Set("element-A")
    source.SetDefaultPrim(root.GetPrim())
    source.GetRootLayer().Export(str(path))
    for name in ("A", "B"):
        root = stage.DefinePrim("/" + name, "Xform")
        root.GetReferences().AddReference(str(path))
    return stage.GetPrimAtPath("/A/Cube"), stage.GetPrimAtPath("/B/Cube")
