"""Scene-scoped issue actions and notifications."""
from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

import carb.settings
import omni.kit.commands
import omni.usd
from pxr import Tf, Usd

from .commands import UpdateIssuesCommand
from .model import CommentRecord, IssueRecord, Status
from .store import IssueStore


class IssueService:
    def __init__(self):
        self._context = omni.usd.get_context()
        self._listeners = []
        self._notice = None
        self._mutating = False
        self.generation = 0
        self.viewport = None
        self._stage_events = self._context.get_stage_event_stream().create_subscription_to_pop(self._stage_changed)
        self._bind_notice()

    @property
    def stage(self):
        return self._context.get_stage() if self._context else None

    @property
    def store(self):
        return IssueStore(self.stage)

    @property
    def author_name(self):
        return carb.settings.get_settings().get("/persistent/exts/issues.tag/authorName") or "Reviewer"

    @author_name.setter
    def author_name(self, value):
        text = value.strip()
        if not text:
            raise ValueError("Enter an author name.")
        carb.settings.get_settings().set("/persistent/exts/issues.tag/authorName", text)

    @property
    def is_dirty(self):
        return bool(self.stage and self.stage.GetRootLayer().dirty)

    def add_listener(self, callback):
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify(self):
        for callback in tuple(self._listeners):
            callback()

    def _bind_notice(self):
        if self._notice:
            self._notice.Revoke()
        self._notice = Tf.Notice.Register(Usd.Notice.ObjectsChanged, self._objects_changed, self.stage) if self.stage else None

    def _objects_changed(self, notice, stage):
        if not self._mutating:
            self._notify()

    def _stage_changed(self, event):
        if event.type in (int(omni.usd.StageEventType.OPENED), int(omni.usd.StageEventType.CLOSED)):
            self.generation += 1
            self._bind_notice()
        self._notify()

    @staticmethod
    def _text(text):
        value = text.strip()
        if not value:
            raise ValueError("Enter a description or comment.")
        return value

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    def mutate(self, operation):
        self.store.require_writable()
        self._mutating = True
        try:
            success, result = omni.kit.commands.execute("UpdateIssuesCommand", stage=self.stage, operation=operation)
        finally:
            self._mutating = False
        if not success:
            self._notify()
            raise ValueError("The issue change could not be applied.")
        self._notify()
        return result

    def list_issues(self):
        return self.store.list_issues()

    def get_issue(self, issue_id):
        return self.store.get_issue(issue_id)

    def create_issue(self, description, anchor=None, viewpoint=None):
        text = self._text(description)
        self.store.require_writable()
        now = self._now()
        record = IssueRecord(str(uuid4()), text, Status.OPEN, self.author_name, now, now, self.author_name,
                             anchor=anchor, related_elements=(anchor.element,) if anchor else (),
                             initial_viewpoint_id=viewpoint.id if viewpoint else "")
        def operation():
            self.store.put_issue(record)
            if viewpoint:
                self.store.put_viewpoint(viewpoint, record.id)
        self.mutate(operation)
        return record.id

    def _update(self, issue_id, **values):
        current = self.get_issue(issue_id)
        record = replace(current, modified_at=self._now(), modified_by=self.author_name, **values)
        self.mutate(lambda: self.store.put_issue(record))

    def set_description(self, issue_id, text):
        self._update(issue_id, description=self._text(text))

    def set_status(self, issue_id, status):
        self._update(issue_id, status=Status(status))

    def add_comment(self, issue_id, text, viewpoint=None):
        current = self.get_issue(issue_id)
        comment = CommentRecord(str(uuid4()), self._text(text), self.author_name, self._now(), viewpoint.id if viewpoint else "")
        record = replace(current, comments=current.comments + (comment,), modified_at=self._now(), modified_by=self.author_name)
        def operation():
            self.store.put_issue(record)
            if viewpoint:
                self.store.put_viewpoint(viewpoint, issue_id)
        self.mutate(operation)
        return comment.id

    def set_related_elements(self, issue_id, refs):
        self._update(issue_id, related_elements=tuple(dict.fromkeys(refs)))

    def reattach(self, issue_id, anchor):
        self._update(issue_id, anchor=anchor)

    def open_issue(self, issue_id):
        record = self.get_issue(issue_id)
        if record.initial_viewpoint_id and self.viewport:
            self.viewport.restore(self.store.get_viewpoint(record.initial_viewpoint_id))

    def focus_related(self, issue_id):
        record = self.get_issue(issue_id)
        if self.viewport:
            self.viewport.focus(record.related_elements)

    def destroy(self):
        if self._notice:
            self._notice.Revoke()
        self._notice = None
        self._stage_events = None
        self._listeners.clear()
        self._context = None
