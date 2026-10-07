"""BCF 2.1/3.0 import and 3.0 export with previewed topic merging."""
import io
import json
import math
import os
import re
import tempfile
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from uuid import UUID
from zipfile import BadZipFile, ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as ET

from .model import CommentRecord, ElementRef, IssueRecord, Status, ViewpointRecord


@dataclass(frozen=True)
class BcfDocument:
    issues: tuple[IssueRecord, ...]
    viewpoints: tuple[ViewpointRecord, ...]
    warnings: tuple[str, ...] = ()
    native_viewpoints: tuple[str, ...] = ()
    viewpoint_topics: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class Conflict:
    key: str
    topic_id: str
    field: str
    local: str
    incoming: str
    baseline: str | None


@dataclass(frozen=True)
class ImportPlan:
    document: BcfDocument
    conflicts: tuple[Conflict, ...]
    stage: object
    expected_records: tuple[IssueRecord, ...]
    frame_signature: tuple = ()
    reference_path: str | None = None
    source_document: BcfDocument | None = None
    viewpoint_frame_signatures: tuple = ()
    viewpoint_options_signatures: tuple = ()


@dataclass(frozen=True)
class ImportSummary:
    created: int
    updated: int
    comments_added: int
    viewpoints_added: int
    viewpoints_updated: int = 0


def _guid(value):
    try:
        return str(UUID(value))
    except (ValueError, TypeError, AttributeError):
        raise ValueError("BCF identifiers must be UUIDs.") from None


def _text(parent, name, required=False):
    value = parent.findtext(name, "")
    if required and not value.strip():
        raise ValueError(f"BCF {name} is required.")
    return value


def _date(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError()
    except ValueError:
        raise ValueError("BCF timestamps require a timezone.") from None
    return value


def _import_date(value, legacy, warnings):
    if legacy:
        try:
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return _date(value)
        if parsed.tzinfo is None:
            warnings.append('BCF 2.1 timestamps without a timezone were interpreted as UTC; the source timezone is unknown.')
            value = parsed.replace(tzinfo=timezone.utc).isoformat()
    return _date(value)


def _import_status(value, legacy):
    if legacy:
        for status in Status:
            if (value or '').strip().casefold() == status.value.casefold():
                return status
    try:
        return Status(value)
    except ValueError:
        raise ValueError('BCF topic has an unsupported status.') from None


def _xml(payload):
    # Decode before scanning so UTF-16 declarations cannot bypass rejection.
    try:
        decoded = payload.decode("utf-16" if payload.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig")
        if re.search(r"<!\s*(DOCTYPE|ENTITY)", decoded, re.I):
            raise ValueError("BCF XML declarations for entities and doctypes are unsupported.")
        return ET.fromstring(decoded)
    except (UnicodeError, ET.ParseError) as error:
        raise ValueError(f"Invalid BCF XML: {error}") from error


def _safe_path(value):
    path = PurePosixPath(value)
    if not value or "\\" in value or path.is_absolute() or any(p in ("..", ".") for p in value.split("/")) or ":" in value:
        raise ValueError("BCF archive contains an unsafe path.")
    return str(path)


def _finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("BCF numeric values must be finite.")
    if isinstance(value, dict):
        for item in value.values():
            _finite(item)
    elif isinstance(value, (tuple, list)):
        for item in value:
            _finite(item)


def _native_view(view, data):
    allowed = {"camera", "clipping_planes", "visibility", "section_state", "coordinate_frame"}
    if not isinstance(data, dict) or set(data) - allowed:
        raise ValueError("Invalid Omniverse viewpoint metadata.")
    _finite(data)
    camera = data.get("camera", {})
    if not isinstance(camera, dict):
        raise ValueError("Invalid native camera.")
    if camera and (len(camera.get("transform", ())) != 16 or camera.get("projection") not in ("perspective", "orthographic")):
        raise ValueError("Invalid native camera transform.")
    if camera:
        numbers = (*camera["transform"], camera.get("horizontal_aperture", 0), camera.get("vertical_aperture", 0), camera.get("focal_length", 0), *camera.get("clipping_range", ()))
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in numbers):
            raise ValueError("Native camera values must be numeric.")
        if min(camera.get("horizontal_aperture", 0), camera.get("vertical_aperture", 0), camera.get("focal_length", 0)) <= 0 or len(camera.get("clipping_range", ())) != 2:
            raise ValueError("Invalid native camera projection.")
    clips = data.get("clipping_planes", ())
    if any(not isinstance(v, (list, tuple)) or len(v) != 4 or any(isinstance(n, bool) or not isinstance(n, (int, float)) for n in v) for v in clips):
        raise ValueError("Invalid native clipping plane.")
    visibility = data.get("visibility", ())
    for entry in visibility:
        if not isinstance(entry, (tuple, list)) or len(entry) != 2:
            raise ValueError("Invalid native visibility.")
        path, token = entry
        if not isinstance(path, str) or not path.startswith("/") or path == "/" or any(path == owned or path.startswith(owned + "/") for owned in ("/Issues", "/Viewport_Markups")) or token not in ("inherited", "invisible"):
            raise ValueError("Native visibility can target model geometry only.")
    frame = data.get("coordinate_frame", {})
    if not isinstance(frame, dict) or frame.get("up_axis", "Z") not in ("Z", "Y") or not isinstance(frame.get("meters_per_unit", 1), (int, float)) or frame.get("meters_per_unit", 1) <= 0:
        raise ValueError("Invalid native coordinate frame.")
    section = data.get("section_state", {})
    if not isinstance(section, dict):
        raise ValueError("Invalid native section state.")
    if section:
        if set(section) != {"enabled", "transform", "size", "faces"} or not isinstance(section["enabled"], bool):
            raise ValueError("Native section state needs enabled, transform, size, and faces.")
        transform, size, faces = section["transform"], section["size"], section["faces"]
        if not isinstance(transform, (list, tuple)) or len(transform) != 16 or not isinstance(size, (list, tuple)) or len(size) != 3:
            raise ValueError("Invalid native section transform or size.")
        numbers = (*transform, *size)
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in numbers):
            raise ValueError("Native section coordinates must be numeric.")
        try:
            from pxr import Gf
            if not all(math.isfinite(float(v)) for v in numbers) or any(v <= 0 for v in size):
                raise ValueError("Native section size must be positive and finite.")
            determinant = Gf.Matrix4d(*transform).GetDeterminant()
            if not math.isfinite(determinant) or determinant == 0:
                raise ValueError("Native section transform must be nonsingular.")
        except (OverflowError, TypeError) as error:
            raise ValueError("Invalid native section coordinates.") from error
        known_faces = {"MIN_X", "MAX_X", "MIN_Y", "MAX_Y", "MIN_Z", "MAX_Z"}
        if not isinstance(faces, (list, tuple)) or any(not isinstance(face, str) or face not in known_faces for face in faces):
            raise ValueError("Invalid native section faces.")
    return replace(view, camera=camera, clipping_planes=tuple(tuple(v) for v in clips), visibility=tuple(tuple(v) for v in visibility), section_state=section, coordinate_frame=frame)


def _component(node):
    origin = node.findtext("OriginatingSystem", "")
    source = node.get("IfcGuid") or node.findtext("AuthoringToolId", "")
    if not source:
        raise ValueError("BCF component has no identifier.")
    if origin.startswith("omniverse-issues:"):
        try:
            data = json.loads(origin[len("omniverse-issues:"):])
            result = ElementRef(**data)
            if not all(isinstance(v, str) for v in asdict(result).values()) or result.source_id != source:
                raise ValueError()
            return result
        except (TypeError, ValueError):
            raise ValueError("Invalid scoped component identity.") from None
    return ElementRef(origin, "", source, "ifc:GlobalId" if node.get("IfcGuid") else "authoring_tool_id", "")


def _vector(node, name):
    child = node.find(name)
    if child is None:
        raise ValueError(f"BCF camera lacks {name}.")
    try:
        values = tuple(float(child.findtext(k)) for k in ("X", "Y", "Z"))
    except (TypeError, ValueError):
        raise ValueError("Invalid BCF vector.") from None
    _finite(values)
    return values


def _normalize(value):
    length = math.sqrt(sum(v*v for v in value))
    if length < 1e-12:
        raise ValueError("BCF camera has a zero direction.")
    return tuple(v/length for v in value)


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def _read_view(root, snapshot, *, legacy=False, warnings=None):
    warnings = warnings if warnings is not None else []
    camera = root.find("PerspectiveCamera")
    perspective = camera is not None
    if camera is None:
        camera = root.find("OrthogonalCamera")
    if camera is None:
        if legacy:
            warnings.append('BCF 2.1 viewpoints without a camera were retained as evidence; camera navigation is unavailable for them.')
            return ViewpointRecord(_guid(root.get('Guid')), snapshot=snapshot, coordinate_frame={'meters_per_unit': 1, 'up_axis': 'Z'})
        raise ValueError("BCF viewpoint requires a camera.")
    eye = _vector(camera, "CameraViewPoint")
    source_direction = _vector(camera, "CameraDirection")
    source_up = _vector(camera, "CameraUpVector")
    direction = _normalize(source_direction)
    right = _normalize(_cross(direction, source_up))
    up = _cross(right, direction)
    try:
        if legacy and camera.find('AspectRatio') is None:
            aspect = 1.0
            if snapshot:
                from PIL import Image
                try:
                    with Image.open(io.BytesIO(snapshot)) as image:
                        if max(image.size) > 16384 or image.width * image.height > 64_000_000:
                            raise ValueError('BCF snapshot is too large to infer camera aspect ratio.')
                        aspect = image.width / image.height
                except OSError as error:
                    raise ValueError('Invalid BCF snapshot image.') from error
            else:
                warnings.append('BCF 2.1 cameras without a snapshot use an assumed 1:1 aspect ratio.')
        else:
            aspect = float(_text(camera, "AspectRatio", True))
        scale = float(_text(camera, "FieldOfView" if perspective else "ViewToWorldScale", True))
    except ValueError:
        raise ValueError("Invalid BCF camera scale.") from None
    if aspect <= 0 or not math.isfinite(aspect) or not math.isfinite(scale) or not (0 < scale < 180 if perspective else scale > 0):
        raise ValueError("Invalid BCF camera scale.")
    vertical = 24.0 if perspective else scale * 10
    focal = vertical / (2*math.tan(math.radians(scale)/2)) if perspective else 50
    transform = [*right, 0, *up, 0, *(-v for v in direction), 0, *eye, 1]
    refs = tuple(_component(v) for v in root.findall("Components/Selection/Component"))
    clips = []
    for plane in root.findall("ClippingPlanes/ClippingPlane"):
        point, normal = _vector(plane, "Location"), _normalize(_vector(plane, "Direction"))
        clips.append((*normal, -sum(a*b for a,b in zip(point, normal))))
    visibility_node = root.find("Components/Visibility")
    visibility = ()
    bcf_visibility = []
    if visibility_node is not None:
        default = visibility_node.get("DefaultVisibility", "false") in ("true", "1")
        bcf_visibility = [asdict(_component(v)) for v in visibility_node.findall("Exceptions/Component")]
    source_camera = {
        "version": "2.1" if legacy else "3.0",
        "position": list(eye), "direction": list(source_direction), "up": list(source_up),
        "field_of_view": scale if perspective else None,
        "view_to_world_scale": None if perspective else scale, "aspect_ratio": aspect,
    }
    return ViewpointRecord(_guid(root.get("Guid")), camera={"projection": "perspective" if perspective else "orthographic", "transform": transform, "horizontal_aperture": vertical*aspect, "vertical_aperture": vertical, "focal_length": focal, "clipping_range": [0.01, 1000000]}, clipping_planes=tuple(clips), visibility=visibility, selection=refs, snapshot=snapshot, coordinate_frame={"meters_per_unit": 1, "up_axis": "Z", "bcf_default_visibility": visibility_node.get("DefaultVisibility", "false") if visibility_node is not None else "true", "bcf_visibility": bcf_visibility, "bcf_has_visibility": visibility_node is not None, "bcf_source_camera": source_camera})


def read_bcf(path):
    try:
        with ZipFile(path) as archive:
            infos = archive.infolist()
            names = [_safe_path(info.filename.rstrip("/")) for info in infos]
            if len(names) != len(set(names)):
                raise ValueError("BCF archive contains duplicate member names.")
            if len(infos) > 10000 or sum(info.file_size for info in infos) > 100*1024*1024:
                raise ValueError("BCF archive exceeds the import limits.")
            members = {info.filename: archive.read(info) for info in infos if not info.is_dir()}
        version = _xml(members.get("bcf.version", b""))
        if version.tag != "Version" or version.get("VersionId") not in ('2.1', '3.0'):
            raise ValueError('Only BCF XML 2.1 and 3.0 are supported.')
        legacy = version.get('VersionId') == '2.1'
        if not legacy and "extensions.xml" not in members:
            raise ValueError("BCF 3.0 requires extensions.xml.")
        if 'extensions.xml' in members:
            _xml(members['extensions.xml'])
        issues, views, warnings, native_ids, viewpoint_topics = [], [], [], [], []
        for filename, payload in sorted(members.items()):
            if not filename.endswith("/markup.bcf"):
                continue
            folder = filename.rsplit("/", 1)[0]
            root = _xml(payload)
            topic = root.find("Topic")
            if topic is None:
                raise ValueError("BCF markup requires Topic.")
            topic_id = _guid(topic.get("Guid"))
            if topic_id != _guid(folder):
                raise ValueError("BCF topic directory does not match its UUID.")
            status = _import_status(topic.get('TopicStatus'), legacy)
            if not topic.get("TopicType"):
                raise ValueError("BCF topic requires TopicType.")
            title = _text(topic, "Title", True)
            created = _import_date(_text(topic, 'CreationDate', True), legacy, warnings)
            author = _text(topic, "CreationAuthor", True)
            topic_views = []
            for entry in (root.findall('Viewpoints') if legacy else topic.findall('Viewpoints/ViewPoint')):
                view_id = _guid(entry.get("Guid"))
                ref = _text(entry, "Viewpoint")
                snapshot_ref = _text(entry, "Snapshot")
                snapshot_name = folder + "/" + _safe_path(snapshot_ref) if snapshot_ref else ""
                if snapshot_name and snapshot_name not in members:
                    raise ValueError("BCF references a missing snapshot.")
                snapshot = members[snapshot_name] if snapshot_name else b""
                if ref:
                    view_name = folder + "/" + _safe_path(ref)
                    if view_name not in members:
                        raise ValueError("BCF references a missing viewpoint.")
                    view = _read_view(_xml(members[view_name]), snapshot, legacy=legacy, warnings=warnings)
                    if view.id != view_id:
                        raise ValueError("BCF viewpoint UUID mismatch.")
                else:
                    view = ViewpointRecord(view_id, snapshot=snapshot, coordinate_frame={"meters_per_unit": 1, "up_axis": "Z"})
                topic_views.append(view)
            comments = []
            for node in (root.findall('Comment') if legacy else topic.findall('Comments/Comment')):
                view = node.find("Viewpoint")
                comment_author = _text(node, 'Author', required=not legacy)
                if not comment_author.strip():
                    comment_author = 'Unknown author'
                    warnings.append('A BCF 2.1 comment has no author; it was retained with Unknown author attribution.')
                comments.append(CommentRecord(_guid(node.get('Guid')), _text(node, 'Comment'), comment_author, _import_date(_text(node, 'Date', True), legacy, warnings), _guid(view.get('Guid')) if view is not None else ''))
            comment_views = {c.viewpoint_id for c in comments if c.viewpoint_id}
            initial = next((v.id for v in topic_views if v.id not in comment_views), "")
            if legacy and not initial:
                initial = next((v.id for v in topic_views if v.camera), '')
                if initial:
                    warnings.append('BCF 2.1 topics without a separate initial view use their first camera viewpoint for issue navigation.')
            related = tuple(dict.fromkeys(ref for v in topic_views for ref in v.selection))
            native_name = folder + "/omniverse.json"
            if native_name in members:
                try:
                    native = json.loads(members[native_name])
                    if set(native) - {"related_elements", "initial_viewpoint_id", "views"}:
                        raise ValueError("Unexpected native metadata fields.")
                    related = tuple(ElementRef(**value) for value in native.get("related_elements", ()))
                    if any(not all(isinstance(v, str) for v in asdict(ref).values()) for ref in related):
                        raise ValueError("Invalid native component identity.")
                    initial = native.get("initial_viewpoint_id", initial)
                    native_ids.extend(v.id for v in topic_views if v.id in native.get('views', {}))
                    topic_views = [_native_view(v, native["views"][v.id]) if v.id in native.get("views", {}) else v for v in topic_views]
                except (TypeError, KeyError, json.JSONDecodeError) as error:
                    raise ValueError("Invalid Omniverse metadata.") from error
                warnings.append("Omniverse native metadata was retained; other tools may ignore it.")
            ids = {v.id for v in topic_views}
            if initial and initial not in ids or comment_views - ids:
                raise ValueError("BCF issue references an absent viewpoint.")
            if any(topic.find(name) is not None for name in ("BimSnippet", "DocumentReferences", "RelatedTopics", "AssignedTo", "DueDate", "Labels")):
                warnings.append('Assignment, due dates, labels, documents, related topics, and BIM snippets are outside the supported import fields.' if legacy else f'Topic {topic_id} contains unsupported optional fields.')
            issues.append(IssueRecord(topic_id, _text(topic, "Description"), status, author, created, _import_date(_text(topic, 'ModifiedDate') or created, legacy, warnings), _text(topic, "ModifiedAuthor") or author, related_elements=related, initial_viewpoint_id=initial, comments=tuple(comments), bcf_topic_id=topic_id, title=title, issue_type=topic.get("TopicType")))
            views.extend(topic_views)
            viewpoint_topics.extend((view.id, topic_id) for view in topic_views)
        document = BcfDocument(tuple(issues), tuple(views), tuple(dict.fromkeys(warnings)), tuple(dict.fromkeys(native_ids)), tuple(viewpoint_topics))
        _validate_document(document)
        return document
    except (BadZipFile, OSError, RuntimeError) as error:
        raise ValueError(f"Cannot read BCF archive: {error}") from error


def export_document(store):
    records = store.list_issues()
    ownership = tuple((view.id, record.bcf_topic_id or record.id) for record in records for view in store.list_viewpoints(record.id))
    linked = (v for r in records for v in (r.initial_viewpoint_id, *(c.viewpoint_id for c in r.comments)) if v)
    view_ids = dict.fromkeys((*linked, *(identity for identity, topic in ownership)))
    views = []
    from .elements import reference_for_prim
    for identity in view_ids:
        view = store.get_viewpoint(identity)
        if view.visibility:
            hidden = []
            for path, token in view.visibility:
                prim = store.stage.GetPrimAtPath(path)
                if prim and token == "invisible":
                    hidden.append(asdict(reference_for_prim(store.stage, prim)))
            frame = dict(view.coordinate_frame, bcf_default_visibility="true", bcf_visibility=hidden, bcf_has_visibility=True)
            view = replace(view, coordinate_frame=frame)
        views.append(view)
    return BcfDocument(records, tuple(views), viewpoint_topics=ownership)


def _validate_document(document):
    topics, views = set(), set()
    for view in document.viewpoints:
        identity = _guid(view.id)
        if identity in views:
            raise ValueError("Duplicate BCF viewpoint UUID.")
        views.add(identity)
        _finite(asdict(view))
    for issue in document.issues:
        topic = _guid(issue.bcf_topic_id or issue.id)
        if topic in topics:
            raise ValueError("Duplicate BCF topic UUID.")
        topics.add(topic)
        _guid(issue.id)
        if not (issue.title or issue.description).strip() or not issue.author.strip():
            raise ValueError("BCF issue needs title and author.")
        Status(issue.status)
        _date(issue.created_at)
        _date(issue.modified_at)
        comments = set()
        for comment in issue.comments:
            cid = _guid(comment.id)
            if cid in comments:
                raise ValueError("Duplicate BCF comment UUID.")
            comments.add(cid)
            _date(comment.created_at)
            if not comment.author.strip():
                raise ValueError("BCF comment needs author.")
        if any(v and v not in views for v in (issue.initial_viewpoint_id, *(c.viewpoint_id for c in issue.comments))):
            raise ValueError("BCF issue references a missing viewpoint.")
    owned = {}
    for ownership in document.viewpoint_topics:
        if not isinstance(ownership, (list, tuple)) or len(ownership) != 2:
            raise ValueError('Invalid BCF viewpoint ownership.')
        view, topic = ownership
        if view not in views or topic not in topics or view in owned:
            raise ValueError('Invalid BCF viewpoint ownership.')
        owned[view] = topic
    for issue in document.issues:
        topic = issue.bcf_topic_id or issue.id
        for identity in (issue.initial_viewpoint_id, *(comment.viewpoint_id for comment in issue.comments)):
            if identity in owned and owned[identity] != topic:
                raise ValueError('BCF viewpoint ownership disagrees with its topic references.')


def _sub(parent, name, value=None, **attrs):
    node = ET.SubElement(parent, name, attrs)
    if value is not None:
        node.text = str(value)
    return node


def _write_vector(parent, name, values):
    node = _sub(parent, name)
    for axis, value in zip(("X", "Y", "Z"), values):
        _sub(node, axis, value)


def _write_component(parent, ref):
    attrs = {"IfcGuid": ref.source_id} if "ifc" in ref.id_kind.lower() and re.fullmatch(r"[0-9A-Za-z_$]{22}", ref.source_id) else {}
    node = _sub(parent, "Component", **attrs)
    _sub(node, "OriginatingSystem", "omniverse-issues:" + json.dumps(asdict(ref), separators=(",", ":")))
    _sub(node, "AuthoringToolId", ref.source_id)


def _to_bcf_vector(values, frame, point=False):
    values = tuple(float(v) for v in values)
    if frame.get("up_axis", "Z") == "Y":
        values = (values[0], -values[2], values[1])
    elif frame.get("up_axis", "Z") != "Z":
        raise ValueError("Unsupported stage up axis.")
    scale = float(frame.get("meters_per_unit", 1)) if point else 1
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("Invalid stage units.")
    return tuple(v*scale for v in values)


def _write_view(view):
    from .bcf_coordinates import export_view
    view = export_view(view)
    root = ET.Element("VisualizationInfo", Guid=_guid(view.id))
    if view.selection or view.coordinate_frame.get("bcf_has_visibility"):
        components = _sub(root, "Components")
    if view.selection:
        selection = _sub(components, "Selection")
        for ref in view.selection:
            _write_component(selection, ref)
    if view.coordinate_frame.get("bcf_has_visibility"):
        default = view.coordinate_frame.get("bcf_default_visibility", "true")
        if default not in ("true", "false", "1", "0"):
            raise ValueError("Invalid BCF visibility default.")
        visibility = _sub(components, "Visibility", DefaultVisibility=default)
        exceptions = view.coordinate_frame.get("bcf_visibility", ())
        if exceptions:
            entries = _sub(visibility, "Exceptions")
            for values in exceptions:
                _write_component(entries, ElementRef(**values))
    camera = view.camera
    transform = camera.get("transform", ())
    if len(transform) != 16:
        raise ValueError("A BCF viewpoint requires a captured camera transform.")
    perspective = camera.get("projection") == "perspective"
    node = _sub(root, "PerspectiveCamera" if perspective else "OrthogonalCamera")
    _write_vector(node, "CameraViewPoint", _to_bcf_vector(transform[12:15], view.coordinate_frame, True))
    _write_vector(node, "CameraDirection", _normalize(_to_bcf_vector(tuple(-v for v in transform[8:11]), view.coordinate_frame)))
    _write_vector(node, "CameraUpVector", _normalize(_to_bcf_vector(transform[4:7], view.coordinate_frame)))
    vertical = float(camera["vertical_aperture"])
    horizontal = float(camera["horizontal_aperture"])
    focal = float(camera.get("focal_length", 50))
    if min(vertical, horizontal, focal) <= 0:
        raise ValueError("Invalid native camera projection.")
    value = math.degrees(2*math.atan(vertical/(2*focal))) if perspective else vertical*.1*float(view.coordinate_frame.get("meters_per_unit", 1))
    _sub(node, "FieldOfView" if perspective else "ViewToWorldScale", value)
    _sub(node, "AspectRatio", horizontal/vertical)
    if view.clipping_planes:
        planes = _sub(root, "ClippingPlanes")
        for values in view.clipping_planes:
            normal = tuple(values[:3])
            length_sq = sum(v*v for v in normal)
            if length_sq == 0:
                raise ValueError("Invalid clipping plane normal.")
            location = tuple(-values[3]*v/length_sq for v in normal)
            plane = _sub(planes, "ClippingPlane")
            _write_vector(plane, "Location", _to_bcf_vector(location, view.coordinate_frame, True))
            _write_vector(plane, "Direction", _normalize(_to_bcf_vector(normal, view.coordinate_frame)))
    return root


def write_bcf(document, path):
    _validate_document(document)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    os.close(descriptor)
    try:
        with ZipFile(temporary, "w", compression=ZIP_DEFLATED) as archive:
            def xml(name, node):
                archive.writestr(name, ET.tostring(node, encoding="utf-8", xml_declaration=True))
            xml("bcf.version", ET.Element("Version", VersionId="3.0"))
            extensions = ET.Element("Extensions")
            types = _sub(extensions, "TopicTypes")
            for name in dict.fromkeys(issue.issue_type for issue in document.issues):
                _sub(types, "TopicType", name)
            statuses = _sub(extensions, "TopicStatuses")
            for status in Status:
                _sub(statuses, "TopicStatus", status.value)
            xml("extensions.xml", extensions)
            views = {v.id: v for v in document.viewpoints}
            for issue in document.issues:
                folder = _guid(issue.bcf_topic_id or issue.id)
                markup = ET.Element("Markup")
                topic = _sub(markup, "Topic", Guid=folder, TopicType=issue.issue_type, TopicStatus=issue.status.value)
                _sub(topic, "Title", issue.title or issue.description.splitlines()[0][:255] or "Issue")
                _sub(topic, "CreationDate", issue.created_at)
                _sub(topic, "CreationAuthor", issue.author)
                _sub(topic, "ModifiedDate", issue.modified_at)
                _sub(topic, "ModifiedAuthor", issue.modified_by or issue.author)
                _sub(topic, "Description", issue.description)
                if issue.comments:
                    comments = _sub(topic, "Comments")
                    for record in issue.comments:
                        comment = _sub(comments, "Comment", Guid=_guid(record.id))
                        _sub(comment, "Date", record.created_at)
                        _sub(comment, "Author", record.author)
                        if record.text:
                            _sub(comment, "Comment", record.text)
                        if record.viewpoint_id:
                            _sub(comment, "Viewpoint", Guid=_guid(record.viewpoint_id))
                owned = (identity for identity, topic_id in document.viewpoint_topics if topic_id == folder)
                ids = tuple(dict.fromkeys(v for v in (issue.initial_viewpoint_id, *(c.viewpoint_id for c in issue.comments), *owned) if v))
                native_views = {}
                if ids:
                    entries = _sub(topic, "Viewpoints")
                    for index, identity in enumerate(ids):
                        view = views[identity]
                        entry = _sub(entries, "ViewPoint", Guid=_guid(identity))
                        if view.camera:
                            _sub(entry, "Viewpoint", identity + ".bcfv")
                            xml(folder + "/" + identity + ".bcfv", _write_view(view))
                        if view.snapshot:
                            suffix = ".png" if view.snapshot.startswith(b"\x89PNG\r\n\x1a\n") else ".jpg" if view.snapshot.startswith(b"\xff\xd8") else None
                            if not suffix:
                                raise ValueError("BCF snapshot must be PNG or JPEG.")
                            _sub(entry, "Snapshot", identity + suffix)
                            archive.writestr(folder + "/" + identity + suffix, view.snapshot)
                        _sub(entry, "Index", index)
                        native_views[identity] = {k: asdict(view)[k] for k in ("camera", "clipping_planes", "visibility", "section_state", "coordinate_frame")}
                xml(folder + "/markup.bcf", markup)
                archive.writestr(folder + "/omniverse.json", json.dumps({"related_elements": [asdict(r) for r in issue.related_elements], "initial_viewpoint_id": issue.initial_viewpoint_id, "views": native_views}, allow_nan=False, separators=(",", ":")))
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def plan_import(document, store, *, reference_path=None, viewpoint_options=None):
    _validate_document(document)
    from .bcf_coordinates import ViewpointImportOptions, import_view, source_view, stage_mapping
    source_document = replace(document, viewpoints=tuple(
        source_view(view) if view.id not in document.native_viewpoints and view.camera and 'bcf_has_visibility' in view.coordinate_frame else view
        for view in document.viewpoints))
    if viewpoint_options is None:
        viewpoint_options = {}
    if not isinstance(viewpoint_options, dict) or any(key not in {v.id for v in document.viewpoints} for key in viewpoint_options):
        raise ValueError('Unknown BCF viewpoint options key.')
    default_options = ViewpointImportOptions(reference_path=reference_path)
    converted, frame_signatures, option_signatures = [], [], []
    mappings = {}
    for view in document.viewpoints:
        options = viewpoint_options.get(view.id, default_options)
        if isinstance(options, dict):
            if any(key not in ('reference_path', 'coordinate_mode', 'fov_mode') for key in options):
                raise ValueError('Unknown BCF viewpoint options key.')
            options = ViewpointImportOptions(**options)
        if not isinstance(options, ViewpointImportOptions):
            raise ValueError('Invalid BCF viewpoint options.')
        explicit_reference = view.id in viewpoint_options and options.reference_path is not None
        options = replace(options, reference_path=options.reference_path if options.reference_path is not None else reference_path)
        standard = view.id not in document.native_viewpoints and view.camera and 'bcf_has_visibility' in view.coordinate_frame
        if options.fov_mode == 'horizontal' and (not standard or view.coordinate_frame.get('bcf_source_camera', {}).get('version') != '2.1' or view.camera.get('projection') != 'perspective'):
            raise ValueError('BCF horizontal FOV requires a standard 2.1 perspective camera.')
        if not standard:
            if view.id in viewpoint_options and (options.coordinate_mode != 'source_world' or explicit_reference):
                raise ValueError('Native or snapshot-only viewpoints cannot change their BCF reference frame.')
            converted.append(view)
            continue
        preserve_mapping = 'bcf_reference_mapping' in view.coordinate_frame and view.id not in viewpoint_options and reference_path is None
        if preserve_mapping:
            anchor = view.coordinate_frame.get('bcf_reference_prim')
            prim = store.stage.GetPrimAtPath(anchor) if anchor else None
            marker = prim.GetAttribute('omni:hoops:metadata:TYPE') if prim else None
            selected = anchor if marker and marker.Get() == 'IFCSITE' else None
            options = ViewpointImportOptions(selected, view.coordinate_frame.get('bcf_coordinate_mode', 'source_world'), view.coordinate_frame.get('bcf_fov_mode', 'file'))
        key = options.reference_path, options.coordinate_mode
        if key not in mappings:
            mappings[key] = stage_mapping(store.stage, reference_path=key[0], coordinate_mode=key[1])
        mapping = mappings[key]
        converted.append(view if preserve_mapping else import_view(view, mapping, options=options))
        frame_signatures.append((view.id, mapping))
        option_signatures.append((view.id, options))
    mapping = mappings.get((reference_path, 'source_world'), next(iter(mappings.values()), ()))
    document = replace(document, viewpoints=tuple(converted))
    existing = store.list_issues()
    topics = {r.bcf_topic_id or r.id: r for r in existing}
    conflicts = []
    for incoming in document.issues:
        topic_id = incoming.bcf_topic_id or incoming.id
        local = topics.get(topic_id)
        if local is None:
            continue
        for field in ("title", "description", "status", "issue_type"):
            current, received = getattr(local, field), getattr(incoming, field)
            current = current.value if isinstance(current, Status) else current
            received = received.value if isinstance(received, Status) else received
            baseline = local.import_baseline.get(field)
            if current != received and (baseline is None or current != baseline and received != baseline):
                conflicts.append(Conflict(topic_id + ":" + field, topic_id, field, current, received, baseline))
    return ImportPlan(document, tuple(conflicts), store.stage, existing, mapping, reference_path,
                      source_document, tuple(frame_signatures), tuple(option_signatures))


def apply_import(plan, choices, service):
    from .bcf_coordinates import stage_mapping
    if service.stage is not plan.stage or service.list_issues() != plan.expected_records:
        raise ValueError("The scene changed after import preview. Preview the file again.")
    if plan.viewpoint_frame_signatures:
        options = dict(plan.viewpoint_options_signatures)
        checked = {}
        for identity, signature in plan.viewpoint_frame_signatures:
            option = options[identity]
            key = option.reference_path, option.coordinate_mode
            if key not in checked:
                checked[key] = stage_mapping(service.stage, reference_path=key[0], coordinate_mode=key[1])
            if checked[key] != signature:
                raise ValueError('The model coordinate frame changed after import preview. Preview the file again.')
    elif plan.frame_signature and stage_mapping(service.stage, reference_path=plan.reference_path) != plan.frame_signature:
        raise ValueError('The model coordinate frame changed after import preview. Preview the file again.')
    for conflict in plan.conflicts:
        if choices.get(conflict.key) not in ("keep_local", "use_imported"):
            raise ValueError("Choose Keep local or Use imported for every conflict.")
    topics = {r.bcf_topic_id or r.id: r for r in plan.expected_records}
    conflicts = {c.key: c for c in plan.conflicts}
    views = {v.id: v for v in plan.document.viewpoints}
    records, pending_views = [], []
    remapped_views = {}
    created = updated = comments_added = 0
    for incoming in plan.document.issues:
        topic_id = incoming.bcf_topic_id or incoming.id
        local = topics.get(topic_id)
        baseline = dict(local.import_baseline) if local else {}
        fields = {}
        for field in ("title", "description", "status", "issue_type"):
            received = getattr(incoming, field)
            received_value = received.value if isinstance(received, Status) else received
            key = topic_id + ":" + field
            if local is None:
                fields[field] = received
                baseline[field] = received_value
            elif key in conflicts:
                fields[field] = received if choices[key] == "use_imported" else getattr(local, field)
                if choices[key] == "use_imported":
                    baseline[field] = received_value
            elif getattr(local, field) == received or baseline.get(field) == (getattr(local, field).value if isinstance(getattr(local, field), Status) else getattr(local, field)):
                fields[field] = received
                baseline[field] = received_value
            else:
                fields[field] = getattr(local, field)
                baseline[field] = received_value
        known_comments = {c.id for c in local.comments} if local else set()
        new_comments = tuple(c for c in incoming.comments if c.id not in known_comments)
        comments_added += len(new_comments)
        if local:
            attribution = {"modified_at": incoming.modified_at, "modified_by": incoming.modified_by} if any(getattr(local, field) != fields[field] for field in fields) or new_comments else {}
            record = replace(local, **fields, **attribution, comments=local.comments + new_comments, bcf_topic_id=topic_id, import_baseline=baseline, related_elements=tuple(dict.fromkeys(local.related_elements + incoming.related_elements)), initial_viewpoint_id=local.initial_viewpoint_id or incoming.initial_viewpoint_id)
            updated += int(record != local)
        else:
            record = replace(incoming, **fields, id=topic_id, bcf_topic_id=topic_id, anchor=None, import_baseline=baseline, number=0)
            created += 1
        records.append(record)
        owned = (view for view, topic in plan.document.viewpoint_topics if topic == topic_id)
        for identity in dict.fromkeys(v for v in (record.initial_viewpoint_id, *(c.viewpoint_id for c in record.comments), *owned) if v):
            if identity not in views:
                continue
            try:
                existing_view = service.store.get_viewpoint(identity)
            except KeyError:
                pending_views.append((record.id, replace(views[identity], markup_path="")))
            else:
                old_mapping = existing_view.coordinate_frame.get('bcf_reference_mapping')
                incoming_view = views[identity]
                frame_keys = ('bcf_reference_mapping', 'bcf_reference_prim', 'bcf_coordinate_mode', 'bcf_fov_mode', 'meters_per_unit', 'up_axis')
                defaults = {'bcf_coordinate_mode': 'source_world', 'bcf_fov_mode': 'file'}
                frame_changed = any(existing_view.coordinate_frame.get(key, defaults.get(key)) != incoming_view.coordinate_frame.get(key, defaults.get(key)) for key in frame_keys)
                if (incoming_view.coordinate_frame.get('bcf_reference_mapping') and identity not in plan.document.native_viewpoints
                        and existing_view.camera and (old_mapping or existing_view.markup_path)
                        and (frame_changed or existing_view.camera != incoming_view.camera or existing_view.clipping_planes != incoming_view.clipping_planes)):
                    if existing_view.markup_path:
                        raise ValueError('An imported viewpoint has editable Markup. Its coordinate frame cannot be changed by BCF reimport.')
                    converted = replace(existing_view, camera=incoming_view.camera, clipping_planes=incoming_view.clipping_planes,
                                        coordinate_frame=incoming_view.coordinate_frame)
                    remapped_views[identity] = (record.id, converted)
    def operation():
        for record in records:
            if record.number <= 0:
                record = replace(record, number=service.store.next_number())
            service.store.put_issue(record)
        for issue_id, view in pending_views:
            service.store.put_viewpoint(view, issue_id)
        for issue_id, view in remapped_views.values():
            service.store.put_viewpoint(view, issue_id)
    if created or updated or pending_views or remapped_views:
        service.mutate(operation)
    return ImportSummary(created, updated, comments_added, len(pending_views), len(remapped_views))
