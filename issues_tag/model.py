"""Persistent review records, independent of the Kit UI."""
from dataclasses import dataclass, field
from enum import Enum


class Status(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


@dataclass(frozen=True)
class ElementRef:
    model_id: str
    instance_path: str
    source_id: str
    id_kind: str = "path"
    prim_path: str = ""


@dataclass(frozen=True)
class Anchor:
    element: ElementRef
    local_position: tuple[float, float, float]
    geometry_digest: str = ""
    confidence: str = "verified"


@dataclass(frozen=True)
class ViewpointRecord:
    id: str
    camera: dict = field(default_factory=dict)
    clipping_planes: tuple = ()
    visibility: tuple = ()
    selection: tuple[ElementRef, ...] = ()
    markup_path: str = ""
    snapshot: bytes = b""
    section_state: dict = field(default_factory=dict)
    coordinate_frame: dict = field(default_factory=dict)


@dataclass(frozen=True)
class CommentRecord:
    id: str
    text: str
    author: str
    created_at: str
    viewpoint_id: str = ""


@dataclass(frozen=True)
class IssueRecord:
    id: str
    description: str
    status: Status
    author: str
    created_at: str
    modified_at: str
    modified_by: str
    anchor: Anchor | None = None
    related_elements: tuple[ElementRef, ...] = ()
    initial_viewpoint_id: str = ""
    comments: tuple[CommentRecord, ...] = ()
    bcf_topic_id: str = ""
    import_baseline: dict = field(default_factory=dict)
