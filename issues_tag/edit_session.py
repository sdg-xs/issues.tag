"""A scene-bound issue draft. Nothing in this object writes USD."""
from dataclasses import dataclass, field, replace
from copy import deepcopy
from uuid import uuid4

from .model import CommentRecord, IssueRecord, Status, ViewpointRecord


@dataclass
class IssueEditSession:
    stage: object
    generation: int
    record: IssueRecord
    original: IssueRecord | None = None
    viewpoint: ViewpointRecord | None = None
    original_viewpoint: ViewpointRecord | None = None
    comment_text: str = ""
    comment_viewpoint: ViewpointRecord | None = None
    comment_viewpoints: dict[str, ViewpointRecord] = field(default_factory=dict)
    original_comment_viewpoints: dict[str, ViewpointRecord] = field(default_factory=dict)

    @classmethod
    def create(cls, service, anchor, issue_type, viewpoint):
        now = service._now()
        record = IssueRecord(str(uuid4()), "", Status.OPEN, service.author_name,
                             now, now, service.author_name, anchor=anchor,
                             related_elements=(anchor.element,) if anchor else (),
                             initial_viewpoint_id=viewpoint.id if viewpoint else "",
                             title="", issue_type=issue_type)
        return cls(service.stage, service.generation, record, viewpoint=viewpoint)

    @classmethod
    def edit(cls, service, issue_id):
        record = service.get_issue(issue_id)
        viewpoint = service.store.get_viewpoint(record.initial_viewpoint_id) if record.initial_viewpoint_id else None
        comments = {comment.id: service.store.get_viewpoint(comment.viewpoint_id)
                    for comment in record.comments if comment.viewpoint_id}
        return cls(service.stage, service.generation, deepcopy(record), record, deepcopy(viewpoint), viewpoint,
                   comment_viewpoints=deepcopy(comments), original_comment_viewpoints=comments)

    @property
    def is_new(self):
        return self.original is None

    @property
    def dirty(self):
        return (self.is_new or self.record != self.original or self.viewpoint != self.original_viewpoint
                or bool(self.comment_text.strip()) or self.comment_viewpoint is not None
                or self.comment_viewpoints != self.original_comment_viewpoints)

    def update(self, **fields):
        self.record = replace(self.record, **fields)

    def stage_comment(self, service):
        self.require_current(service)
        text = self.comment_text.strip()
        if not text:
            raise ValueError('Enter comment text before adding its evidence.')
        comment = CommentRecord(str(uuid4()), text, service.author_name, service._now(),
                                self.comment_viewpoint.id if self.comment_viewpoint else '')
        self.update(comments=self.record.comments + (comment,))
        if self.comment_viewpoint:
            self.comment_viewpoints[comment.id] = self.comment_viewpoint
        self.comment_text, self.comment_viewpoint = '', None
        return comment.id

    def set_comment_viewpoint(self, comment_id, viewpoint):
        if not any(comment.id == comment_id for comment in self.record.comments):
            raise ValueError('This comment is no longer in the draft.')
        self.update(comments=tuple(replace(comment, viewpoint_id=viewpoint.id) if comment.id == comment_id else comment
                                   for comment in self.record.comments))
        self.comment_viewpoints[comment_id] = viewpoint

    def require_current(self, service):
        if service.stage != self.stage or service.generation != self.generation:
            raise ValueError("The scene changed. This draft cannot be saved.")
        try:
            if self.original is not None and service.get_issue(self.original.id) != self.original:
                raise ValueError("This issue changed while you were editing it. Discard the draft and reopen it.")
            if self.original_viewpoint is not None and service.store.get_viewpoint(self.original_viewpoint.id) != self.original_viewpoint:
                raise ValueError("The saved evidence changed while you were editing it. Discard the draft and reopen it.")
            for original in self.original_comment_viewpoints.values():
                if service.store.get_viewpoint(original.id) != original:
                    raise ValueError('The saved comment evidence changed while you were editing it.')
        except KeyError:
            raise ValueError("This issue or its saved evidence no longer exists. Discard the draft and reopen it.") from None
