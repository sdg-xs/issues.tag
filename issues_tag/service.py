"""Scene-scoped issue actions and notifications."""
from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

import carb.settings
import omni.kit.commands
import omni.usd
from pxr import Tf, Usd

from .commands import UpdateIssuesCommand
from .model import CommentRecord, Status
from .store import IssueStore


class IssueService:
    def __init__(self):
        self._context = omni.usd.get_context()
        self._listeners = []
        self._notice = None
        self._mutating = False
        self.generation = 0
        self.viewport = None
        self.native_view_recaller = None
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
            def migrated_operation():
                self.store.migrate()
                return operation()
            success, result = omni.kit.commands.execute("UpdateIssuesCommand", stage=self.stage, operation=migrated_operation)
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

    def create_issue(self, description, anchor=None, viewpoint=None, *, title=None, issue_type="Default"):
        from .edit_session import IssueEditSession
        session = IssueEditSession.create(self, anchor, issue_type, viewpoint)
        session.update(title=title if title is not None else description.splitlines()[0] if description else "",
                       description=description)
        return self.commit_session(session)

    def _update(self, issue_id, **values):
        current = self.get_issue(issue_id)
        record = replace(current, modified_at=self._now(), modified_by=self.author_name, **values)
        self.mutate(lambda: self.store.put_issue(record))

    def set_description(self, issue_id, text):
        self._update(issue_id, description=text.strip())

    def list_types(self):
        return self.store.list_types()

    def create_type(self, name):
        self.store.require_writable()
        name = self.store.validate_new_type(name)
        return self.mutate(lambda: self.store.add_type(name))

    def delete_type(self, name, replacement=None):
        store = self.store
        store.require_writable()
        types = store.list_types()
        if name == 'Default':
            raise ValueError('Default cannot be deleted.')
        if name not in types:
            raise ValueError('The selected issue type no longer exists.')
        affected = tuple(record for record in store.list_issues() if record.issue_type == name)
        if replacement is not None and (replacement == name or replacement not in types):
            raise ValueError('Select another existing issue type as the replacement.')
        if affected and replacement is None:
            raise ValueError('Choose a replacement for issues using this type.')

        def operation():
            now = self._now()
            for record in affected:
                store.put_issue(replace(record, issue_type=replacement, modified_at=now, modified_by=self.author_name))
            store.remove_type(name)

        return self.mutate(operation)

    def commit_session(self, session):
        session.require_current(self)
        title = session.record.title.strip()
        if not title or len(title) > 255:
            raise ValueError("Enter an issue title of 1 to 255 characters.")
        if session.record.issue_type not in self.list_types():
            raise ValueError("Select a project issue type.")
        if session.comment_viewpoint is not None and not session.comment_text.strip():
            raise ValueError('Enter comment text before saving its evidence.')
        now = self._now()
        record = replace(session.record, title=title, description=session.record.description.strip(),
                         modified_at=now, modified_by=self.author_name,
                         number=self.store.next_number() if session.is_new else session.original.number,
                         initial_viewpoint_id=session.viewpoint.id if session.viewpoint else session.record.initial_viewpoint_id)
        if session.comment_text.strip():
            comment = CommentRecord(str(uuid4()), session.comment_text.strip(), self.author_name, now,
                                    session.comment_viewpoint.id if session.comment_viewpoint else "")
            record = replace(record, comments=record.comments + (comment,))
        def operation():
            self.store.put_issue(record)
            if session.viewpoint is not None and session.viewpoint != session.original_viewpoint:
                self.store.put_viewpoint(session.viewpoint, record.id)
            for comment_id, viewpoint in session.comment_viewpoints.items():
                if viewpoint != session.original_comment_viewpoints.get(comment_id):
                    self.store.put_viewpoint(viewpoint, record.id)
            if session.comment_viewpoint is not None:
                self.store.put_viewpoint(session.comment_viewpoint, record.id)
        self.mutate(operation)
        return record.id

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
            self.restore_viewpoint(self.store.get_viewpoint(record.initial_viewpoint_id))

    def restore_viewpoint(self, record):
        if not self.viewport:
            raise ValueError('The saved view needs a viewport in the current scene.')
        if self.native_view_recaller and self.native_view_recaller(record):
            return True
        self.viewport.restore(record)
        return False

    def focus_related(self, issue_id):
        record = self.get_issue(issue_id)
        if self.viewport:
            self.viewport.focus(record.related_elements)

    def destroy(self):
        errors = []
        notice, self._notice = self._notice, None
        try:
            if notice:
                notice.Revoke()
        except Exception as error:
            errors.append(error)
        self._stage_events = None
        listeners, self._listeners = self._listeners, []
        try:
            listeners.clear()
        except Exception as error:
            errors.append(error)
        self.native_view_recaller = None
        self._context = None
        if errors:
            raise ExceptionGroup('Issue service cleanup failed', errors)
