"""File exchange behavior against real USD stores and official BCF schemas."""
import importlib.util
import base64
from dataclasses import replace
from uuid import uuid4
from zipfile import ZipFile

from verify_kit import ROOT


def bcf_api():
    assert importlib.util.find_spec("issues_tag.bcf"), "BCF file exchange is not implemented"
    from issues_tag import bcf
    return bcf


def evidence():
    from issues_tag.model import ElementRef, ViewpointRecord
    return ViewpointRecord(str(uuid4()), camera={"projection": "perspective", "transform": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 2, 3, 4, 1], "horizontal_aperture": 36, "vertical_aperture": 24, "focal_length": 50, "clipping_range": [0.1, 1000]}, coordinate_frame={"meters_per_unit": 1, "up_axis": "Z"}, selection=(ElementRef("missing.ifc", "/Building", "0123456789012345678901", "ifc:GlobalId", "/Building/Wall"),), snapshot=base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aZHsAAAAASUVORK5CYII="))


async def test_bcf_round_trip_supported_fields(service):
    bcf = bcf_api()
    first, second = evidence(), evidence()
    service.author_name = "Reviewer A"
    issue_id = service.create_issue("Door overlaps wall\nCheck clearance", viewpoint=first)
    service.add_comment(issue_id, "Annotated evidence", second)
    service.set_related_elements(issue_id, first.selection)
    other_id = service.create_issue("Independent ceiling issue", viewpoint=evidence())
    path = ROOT / "verification" / "roundtrip.bcf"
    bcf.write_bcf(bcf.export_document(service.store), path)
    document = bcf.read_bcf(path)
    issue = next(r for r in document.issues if r.id == issue_id)
    assert issue.id == issue_id and issue.description == "Door overlaps wall\nCheck clearance"
    assert issue.author == "Reviewer A" and issue.comments[0].text == "Annotated evidence"
    assert issue.related_elements[0].source_id == "0123456789012345678901"
    assert issue.anchor is None
    assert len(document.viewpoints) == 3 and all(v.snapshot == first.snapshot for v in document.viewpoints)
    from lxml import etree
    with ZipFile(path) as archive:
        for name in archive.namelist():
            schema = "markup" if name.endswith("markup.bcf") else "visinfo" if name.endswith(".bcfv") else "version" if name == "bcf.version" else "extensions" if name == "extensions.xml" else None
            if schema:
                validator = etree.XMLSchema(etree.parse(str(ROOT / "tests" / "bcf_schemas" / (schema + ".xsd"))))
                validator.assertValid(etree.fromstring(archive.read(name)))
    from test_persistence import service_for_new_scene
    service = await service_for_new_scene()
    bcf.apply_import(bcf.plan_import(document, service.store), {}, service)
    assert len(service.list_issues()) == 2 and service.get_issue(other_id).description == "Independent ceiling issue"
    assert service.get_issue(issue_id).anchor is None, "Unresolved BCF components produced a misleading pin"
    assert service.store.get_viewpoint(issue.initial_viewpoint_id).snapshot == first.snapshot
    bcf.apply_import(bcf.plan_import(document, service.store), {}, service)
    assert len(service.get_issue(issue_id).comments) == 1 and len(bcf.export_document(service.store).viewpoints) == 3


async def test_repeat_import_and_conflict_choices(service):
    bcf = bcf_api()
    from issues_tag.model import IssueRecord, Status, CommentRecord
    topic = str(uuid4())
    comment = CommentRecord(str(uuid4()), "Imported evidence", "Partner", "2026-09-01T12:00:00+00:00")
    incoming = IssueRecord(topic, "Original", Status.OPEN, "Partner", comment.created_at, comment.created_at, "Partner", comments=(comment,), bcf_topic_id=topic)
    document = bcf.BcfDocument((incoming,), ())
    bcf.apply_import(bcf.plan_import(document, service.store), {}, service)
    bcf.apply_import(bcf.plan_import(document, service.store), {}, service)
    assert len(service.list_issues()) == 1 and len(service.get_issue(topic).comments) == 1
    service.set_description(topic, "Local edit")
    service.set_status(topic, Status.RESOLVED)
    changed = bcf.BcfDocument((replace(incoming, description="Partner edit", status=Status.CLOSED, modified_at="2026-09-02T12:00:00+00:00", modified_by="Partner editor"),), ())
    plan = bcf.plan_import(changed, service.store)
    assert {c.field for c in plan.conflicts} == {"description", "status"}
    assert service.get_issue(topic).description == "Local edit", "Preview mutated local issues"
    try:
        bcf.apply_import(plan, {}, service)
    except ValueError:
        pass
    else:
        raise AssertionError("Conflicting import accepted without choices")
    bcf.apply_import(plan, {c.key: "keep_local" for c in plan.conflicts}, service)
    assert service.get_issue(topic).description == "Local edit"
    plan = bcf.plan_import(changed, service.store)
    bcf.apply_import(plan, {c.key: "use_imported" for c in plan.conflicts}, service)
    assert service.get_issue(topic).description == "Partner edit" and service.get_issue(topic).status == Status.CLOSED
    assert service.get_issue(topic).modified_by == "Partner editor" and service.get_issue(topic).modified_at == "2026-09-02T12:00:00+00:00", "Imported field updates lost modification attribution"


async def test_import_preview_rejects_stale_scene(service):
    bcf = bcf_api()
    issue_id = service.create_issue("Original")
    document = bcf.export_document(service.store)
    plan = bcf.plan_import(document, service.store)
    service.set_description(issue_id, "Changed after preview")
    try:
        bcf.apply_import(plan, {}, service)
    except ValueError:
        pass
    else:
        raise AssertionError("Stale import preview overwrote an edit")
    assert service.get_issue(issue_id).description == "Changed after preview"


async def test_invalid_archive_has_no_partial_import(service):
    bcf = bcf_api()
    path = ROOT / "verification" / "invalid.bcf"
    cases = [("../escape.xml", b"<Version VersionId='3.0'/>") , ("bcf.version", b"<Version VersionId='2.1'/>"), ("bcf.version", b"<!DOCTYPE Version [<!ENTITY x SYSTEM 'file:///secret'>]><Version VersionId='3.0'/>"), ("bcf.version", b"<broken")]
    for name, payload in cases:
        with ZipFile(path, "w") as archive:
            archive.writestr(name, payload)
        try:
            bcf.read_bcf(path)
        except ValueError:
            pass
        else:
            raise AssertionError("Unsafe or unsupported archive was accepted")
    assert not service.list_issues()


async def test_standard_camera_coordinates_without_native_metadata(service):
    bcf = bcf_api()
    view = evidence()
    view = replace(view, coordinate_frame={"meters_per_unit": 0.01, "up_axis": "Y"})
    service.create_issue("Centimetre Y-up model", viewpoint=view)
    path = ROOT / "verification" / "standard-coordinates.bcf"
    bcf.write_bcf(bcf.export_document(service.store), path)
    with ZipFile(path) as archive:
        members = {name: archive.read(name) for name in archive.namelist() if not name.endswith("omniverse.json")}
    with ZipFile(path, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    document = bcf.read_bcf(path)
    transform = document.viewpoints[0].camera["transform"]
    assert tuple(transform[12:15]) == (0.02, -0.04, 0.03), "BCF camera did not convert centimetres/Y-up to metres/Z-up"
    assert tuple(transform[8:11]) == (0.0, -1.0, 0.0)


async def test_archive_duplicates_limits_and_native_metadata_are_rejected(service):
    bcf = bcf_api()
    path = ROOT / "verification" / "invalid-boundaries.bcf"
    with ZipFile(path, "w") as archive:
        archive.writestr("bcf.version", b"<Version VersionId='3.0'/>")
        archive.writestr("bcf.version", b"<Version VersionId='3.0'/>")
    try:
        bcf.read_bcf(path)
    except ValueError:
        pass
    else:
        raise AssertionError("Duplicate archive member was accepted")
    service.create_issue("Native metadata", viewpoint=evidence())
    bcf.write_bcf(bcf.export_document(service.store), path)
    with ZipFile(path) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    import json
    native_name = next(n for n in members if n.endswith("omniverse.json"))
    native = json.loads(members[native_name])
    first = next(iter(native["views"].values()))
    first["visibility"] = [["/Issues", "invisible"]]
    members[native_name] = json.dumps(native).encode()
    with ZipFile(path, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    try:
        bcf.read_bcf(path)
    except ValueError:
        pass
    else:
        raise AssertionError("Imported native visibility could target issue storage")


async def test_missing_referenced_snapshot_is_reported(service):
    bcf = bcf_api()
    service.create_issue("Snapshot evidence", viewpoint=evidence())
    path = ROOT / "verification" / "missing-snapshot.bcf"
    bcf.write_bcf(bcf.export_document(service.store), path)
    with ZipFile(path) as archive:
        members = {name: archive.read(name) for name in archive.namelist() if not name.endswith(".png")}
    with ZipFile(path, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    try:
        bcf.read_bcf(path)
    except ValueError:
        pass
    else:
        raise AssertionError("Missing referenced evidence was silently dropped")


async def test_external_visibility_survives_export_without_native_metadata(service):
    bcf = bcf_api()
    service.create_issue("Visibility evidence", viewpoint=evidence())
    path = ROOT / "verification" / "external-visibility.bcf"
    bcf.write_bcf(bcf.export_document(service.store), path)
    from xml.etree import ElementTree as ET
    with ZipFile(path) as archive:
        members = {name: archive.read(name) for name in archive.namelist() if not name.endswith("omniverse.json")}
    name = next(n for n in members if n.endswith(".bcfv"))
    root = ET.fromstring(members[name])
    components = root.find("Components")
    visibility = ET.SubElement(components, "Visibility", DefaultVisibility="false")
    exceptions = ET.SubElement(visibility, "Exceptions")
    ET.SubElement(exceptions, "Component", IfcGuid="0123456789012345678901")
    members[name] = ET.tostring(root)
    with ZipFile(path, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    document = bcf.read_bcf(path)
    bcf.write_bcf(document, path)
    with ZipFile(path) as archive:
        root = ET.fromstring(archive.read(next(n for n in archive.namelist() if n.endswith(".bcfv"))))
    visibility = root.find("Components/Visibility")
    assert visibility is not None and visibility.get("DefaultVisibility") == "false", "External visibility default was lost"
    assert visibility.find("Exceptions/Component").get("IfcGuid") == "0123456789012345678901"
    assert bcf.read_bcf(path).viewpoints[0].visibility == (), "Unresolved visibility was treated as native model paths"


async def test_import_rejects_malformed_native_section_state(service):
    bcf = bcf_api()
    import json
    service.create_issue("Section evidence", viewpoint=evidence())
    path = ROOT / "verification" / "invalid-section.bcf"
    bcf.write_bcf(bcf.export_document(service.store), path)
    with ZipFile(path) as archive:
        original = {name: archive.read(name) for name in archive.namelist()}
    native_name = next(n for n in original if n.endswith("omniverse.json"))
    valid = {"enabled": True, "transform": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1], "size": [2, 3, 4], "faces": ["MIN_X", "MAX_X"]}
    malformed = [{"enabled": True}, dict(valid, enabled="yes"), dict(valid, transform=[0]*16), dict(valid, transform=[1]*15), dict(valid, size=[2, 0, 4]), dict(valid, size=[2, 3]), dict(valid, faces=["UNKNOWN"])]
    for section in malformed:
        native = json.loads(original[native_name])
        next(iter(native["views"].values()))["section_state"] = section
        with ZipFile(path, "w") as archive:
            for name, data in original.items():
                archive.writestr(name, json.dumps(native).encode() if name == native_name else data)
        try:
            bcf.read_bcf(path)
        except ValueError:
            pass
        else:
            raise AssertionError("Malformed native section state was accepted before viewpoint restoration")
