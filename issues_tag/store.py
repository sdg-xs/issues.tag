"""Versioned issue data embedded in the parent USD root layer."""
import base64
import json
import os
from dataclasses import asdict

from pxr import Sdf, Usd

from .model import Anchor, CommentRecord, ElementRef, IssueRecord, Status, ViewpointRecord


def encode(record):
    values = asdict(record)
    if "snapshot" in values:
        values["snapshot"] = base64.b64encode(values["snapshot"]).decode("ascii")
    return json.dumps(values, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def element(values):
    return ElementRef(**values)


def decode_issue(text):
    data = json.loads(text)
    data["status"] = Status(data["status"])
    if data.get("anchor"):
        anchor = data["anchor"]
        anchor["element"] = element(anchor["element"])
        anchor["local_position"] = tuple(anchor["local_position"])
        data["anchor"] = Anchor(**anchor)
    data["related_elements"] = tuple(element(v) for v in data.get("related_elements", ()))
    data["comments"] = tuple(CommentRecord(**v) for v in data.get("comments", ()))
    return IssueRecord(**data)


def decode_viewpoint(text):
    data = json.loads(text)
    data["snapshot"] = base64.b64decode(data.get("snapshot", ""), validate=True)
    data["selection"] = tuple(element(v) for v in data.get("selection", ()))
    for key in ("clipping_planes", "visibility"):
        data[key] = tuple(tuple(v) for v in data.get(key, ()))
    return ViewpointRecord(**data)


class IssueStore:
    def __init__(self, stage):
        self.stage = stage

    def require_writable(self):
        if self.stage is None:
            raise ValueError("Open a USD scene before editing issues.")
        layer = self.stage.GetRootLayer()
        local_read_only = layer.realPath and os.path.isfile(layer.realPath) and not os.access(layer.realPath, os.W_OK)
        if not layer.permissionToEdit or (not layer.anonymous and not layer.permissionToSave) or local_read_only:
            raise ValueError("The parent scene is read-only. Save a writable copy to edit issues.")
        self._check_version()

    def _check_version(self):
        prim = self.stage.GetPrimAtPath("/Issues") if self.stage else None
        if prim:
            version = prim.GetAttribute("issues:schemaVersion")
            if not version or version.Get() != 1:
                raise ValueError("This scene contains an unsupported issue schema.")

    @staticmethod
    def _safe_name(record_id, prefix):
        import uuid
        try:
            return prefix + uuid.UUID(record_id).hex
        except (ValueError, AttributeError):
            raise ValueError("Issue and viewpoint identifiers must be UUIDs.") from None

    def _container(self):
        prim = self.stage.DefinePrim("/Issues", "Scope")
        prim.CreateAttribute("issues:schemaVersion", Sdf.ValueTypeNames.Int, custom=True).Set(1)
        return prim

    def list_issues(self):
        if self.stage is None:
            return ()
        self._check_version()
        parent = self.stage.GetPrimAtPath("/Issues")
        records = []
        if parent:
            for prim in parent.GetChildren():
                attr = prim.GetAttribute("issues:record")
                if attr:
                    try:
                        records.append(decode_issue(attr.Get()))
                    except (TypeError, ValueError, KeyError) as error:
                        raise ValueError(f"Issue record {prim.GetPath()} is invalid: {error}") from error
        return tuple(sorted(records, key=lambda r: (r.created_at, r.id)))

    def get_issue(self, issue_id):
        for record in self.list_issues():
            if record.id == issue_id:
                return record
        raise KeyError("The selected issue no longer exists.")

    def put_issue(self, record):
        self.require_writable()
        payload = encode(record)
        with Usd.EditContext(self.stage, self.stage.GetRootLayer()):
            self._container()
            path = "/Issues/" + self._safe_name(record.id, "Issue_")
            prim = self.stage.DefinePrim(path, "Scope")
            prim.CreateAttribute("issues:record", Sdf.ValueTypeNames.String, custom=True).Set(payload)
            for key, value in (("id", record.id), ("description", record.description), ("status", record.status.value)):
                prim.CreateAttribute("issues:" + key, Sdf.ValueTypeNames.String, custom=True).Set(value)

    def put_viewpoint(self, viewpoint, issue_id=""):
        self.require_writable()
        payload = encode(viewpoint)
        if not issue_id:
            matches = [r.id for r in self.list_issues() if r.initial_viewpoint_id == viewpoint.id or any(c.viewpoint_id == viewpoint.id for c in r.comments)]
            if len(matches) != 1:
                raise ValueError("A viewpoint must belong to one issue.")
            issue_id = matches[0]
        self.get_issue(issue_id)
        path = "/Issues/" + self._safe_name(issue_id, "Issue_") + "/" + self._safe_name(viewpoint.id, "View_")
        with Usd.EditContext(self.stage, self.stage.GetRootLayer()):
            prim = self.stage.DefinePrim(path, "Scope")
            prim.CreateAttribute("issues:viewpoint", Sdf.ValueTypeNames.String, custom=True).Set(payload)
            if viewpoint.markup_path:
                prim.CreateRelationship("issues:markup", custom=True).SetTargets([viewpoint.markup_path])

    def get_viewpoint(self, viewpoint_id):
        self._check_version()
        for prim in self.stage.Traverse():
            if not str(prim.GetPath()).startswith("/Issues/"):
                continue
            attr = prim.GetAttribute("issues:viewpoint")
            if attr:
                record = decode_viewpoint(attr.Get())
                if record.id == viewpoint_id:
                    return record
        raise KeyError("The saved viewpoint no longer exists.")
