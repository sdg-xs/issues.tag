import importlib.util
from pxr import Gf, Sdf, UsdGeom
from fixtures import two_buildings


def require_elements():
    assert importlib.util.find_spec("issues_tag.elements") is not None, "Element attachment is not implemented"


def test_pin_follows_transform_and_instance_scope(service):
    require_elements()
    from issues_tag.elements import make_anchor, world_anchor, resolve_element
    first, second = two_buildings(service.stage)
    a = make_anchor(service.stage, str(first.GetPath()), (0, 0, 1))
    b = make_anchor(service.stage, str(second.GetPath()), (0, 0, 1))
    UsdGeom.Xformable(service.stage.GetPrimAtPath("/A")).AddTranslateOp().Set(Gf.Vec3d(10, 20, 30))
    assert world_anchor(service.stage, a) == (10, 20, 31)
    assert world_anchor(service.stage, b) == (0, 0, 1)
    assert resolve_element(service.stage, a.element).prim_path == "/A/Cube"
    assert resolve_element(service.stage, b.element).prim_path == "/B/Cube"
    UsdGeom.Xformable(service.stage.GetPrimAtPath("/A")).AddScaleOp().Set(Gf.Vec3f(2, 2, 2))
    assert world_anchor(service.stage, a) == (10, 20, 32)
    UsdGeom.Xformable(service.stage.GetPrimAtPath("/A")).AddRotateXOp().Set(90)
    rotated = world_anchor(service.stage, a)
    assert all(abs(actual - expected) < 1e-6 for actual, expected in zip(rotated, (10, 18, 30)))
    assert world_anchor(service.stage, b) == (0, 0, 1)


def test_revision_matching_and_manual_repair(service):
    require_elements()
    from issues_tag.elements import make_anchor, resolve_element, attachment_state
    first, _ = two_buildings(service.stage)
    anchor = make_anchor(service.stage, "/A/Cube", (0, 0, 1))
    issue_id = service.create_issue("Review cube", anchor)
    first.SetActive(False)
    replacement = UsdGeom.Cube.Define(service.stage, "/A/Renamed").GetPrim()
    replacement.CreateAttribute("ifc:GlobalId", Sdf.ValueTypeNames.String).Set("element-A")
    assert resolve_element(service.stage, anchor.element).prim_path == "/A/Renamed"
    UsdGeom.Cube(replacement).GetSizeAttr().Set(9)
    assert attachment_state(service.stage, anchor) == "needs_review"
    duplicate = UsdGeom.Cube.Define(service.stage, "/A/Duplicate").GetPrim()
    duplicate.CreateAttribute("ifc:GlobalId", Sdf.ValueTypeNames.String).Set("element-A")
    assert resolve_element(service.stage, anchor.element).state == "ambiguous"
    duplicate.SetActive(False)
    service.reattach(issue_id, make_anchor(service.stage, "/A/Renamed", (0, 0, 4.5)))
    assert attachment_state(service.stage, service.get_issue(issue_id).anchor) == "verified"
    replacement.SetActive(False)
    assert resolve_element(service.stage, anchor.element).state == "missing"


def test_related_list_does_not_move_anchor(service):
    require_elements()
    from issues_tag.elements import make_anchor, reference_for_prim
    first, second = two_buildings(service.stage)
    anchor = make_anchor(service.stage, "/A/Cube", (0, 0, 1))
    issue_id = service.create_issue("Related components", anchor)
    service.set_related_elements(issue_id, (anchor.element, reference_for_prim(service.stage, "/B/Cube")))
    service.set_related_elements(issue_id, ())
    assert service.get_issue(issue_id).anchor == anchor


def test_reference_identity_rejects_different_source_model(service):
    from dataclasses import replace
    from issues_tag.elements import make_anchor, resolve_element
    two_buildings(service.stage)
    anchor = make_anchor(service.stage, '/A/Cube', (0, 0, 1))
    other_model = replace(anchor.element, model_id=anchor.element.model_id + '.different')
    assert resolve_element(service.stage, other_model).state == 'missing', 'Same instance and element ID must not match a different source model'
