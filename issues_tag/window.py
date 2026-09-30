"""Compact native review dock using the same actions as integration tests."""

import asyncio
import inspect

import omni.ui as ui

from .model import Status
from .elements import attachment_state, resolve_element
from .styles import STYLE


class IssuesWindow:
    def __init__(self, service, *, on_place_pin=None, on_add_viewpoint=None,
                 on_markup=None, on_import=None, on_export=None, on_add_related=None):
        self.service = service
        self._callbacks = {"place": on_place_pin, "capture": on_add_viewpoint,
                           "markup": on_markup, "import": on_import,
                           "export": on_export, "related": on_add_related}
        self.selected_issue_id = None
        self.pending_viewpoint = None
        self._stage = service.stage
        self._destroyed = False
        self._tasks = set()
        self._image_providers = {}
        self._snapshot_windows = {}
        self._description_record = None
        self._shown_content = None
        self._error = ""
        self.load_error = ""
        self.description = ui.SimpleStringModel("")
        self.comment = ui.SimpleStringModel("")
        self.author = ui.SimpleStringModel(service.author_name)
        self.window = ui.Window("Issues", width=420, height=720)
        self.window.frame.style = STYLE
        self.window.frame.set_build_fn(self._build)
        service.add_listener(self.refresh)
        self.window.frame.rebuild()

    def show(self):
        self.window.visible = True

    def destroy(self):
        if self._destroyed:
            return
        self._destroyed = True
        self.service.remove_listener(self.refresh)
        for task in tuple(self._tasks):
            task.cancel()
        self._tasks.clear()
        self._clear_evidence()
        self.window.destroy()

    def _clear_evidence(self):
        for window in self._snapshot_windows.values():
            window.destroy()
        self._snapshot_windows.clear()
        self._image_providers.clear()

    def refresh(self, *args):
        if self._destroyed:
            return
        if self._stage is not self.service.stage:
            self._clear_evidence()
            self._stage = self.service.stage
            self.selected_issue_id = None
            self.pending_viewpoint = None
            self.description.set_value("")
            self.comment.set_value("")
            self._description_record = None
        records = self._read_records()
        if self.selected_issue_id and not any(r.id == self.selected_issue_id for r in records):
            self.selected_issue_id = None
            self.pending_viewpoint = None
            self._description_record = None
            self.description.set_value("")
            self.comment.set_value("")
        if self.selected_issue_id:
            record = self.service.get_issue(self.selected_issue_id)
            if self.description.as_string == self._description_record:
                self.description.set_value(record.description)
            self._description_record = record.description
        attachment = ""
        related_state = ()
        if self.selected_issue_id:
            attachment = attachment_state(self.service.stage, record.anchor) if record.anchor else "unattached"
            related_state = tuple(resolve_element(self.service.stage, element).state for element in record.related_elements)
        signature = (self._stage, records, self.selected_issue_id, self.pending_viewpoint, attachment, related_state,
                     self._error, self.load_error, self.service.author_name, self.service.is_dirty)
        if signature == self._shown_content:
            return
        self._shown_content = signature
        self.window.frame.rebuild()

    def _read_records(self):
        try:
            records = self.service.list_issues() if self.service.stage else ()
            self.load_error = ""
            return records
        except ValueError as exc:
            self.load_error = str(exc)
            return ()

    def select_issue(self, issue_id):
        record = self.service.get_issue(issue_id)
        changed = self.selected_issue_id != issue_id
        self.selected_issue_id = issue_id
        self.description.set_value(record.description)
        self._description_record = record.description
        if changed:
            self.pending_viewpoint = None
            self.comment.set_value("")
        self.service.open_issue(issue_id)
        self.refresh()

    @staticmethod
    def _text(text):
        value = text.strip()
        if not value:
            raise ValueError("Enter a description or comment.")
        return value

    def _selected(self):
        if not self.selected_issue_id:
            raise ValueError("Select an issue first.")
        return self.service.get_issue(self.selected_issue_id)

    def create_record(self, description):
        issue_id = self.service.create_issue(self._text(description))
        self.select_issue(issue_id)
        return issue_id

    def submit_description(self, text):
        record = self._selected()
        value = self._text(text)
        self.service.set_description(record.id, value)
        self.description.set_value(value)
        self._description_record = value
        self.refresh()

    def submit_comment(self, text):
        record = self._selected()
        comment_id = self.service.add_comment(record.id, self._text(text), self.pending_viewpoint)
        self.pending_viewpoint = None
        self.comment.set_value("")
        self.refresh()
        return comment_id

    def change_status(self, status):
        self.service.set_status(self._selected().id, Status(status))

    def _call(self, callback, *args):
        try:
            result = callback(*args)
            if inspect.isawaitable(result):
                self._schedule(result)
            self._error = ""
        except Exception as exc:
            self._error = str(exc)
        self.refresh()

    def _schedule(self, coroutine):
        task = asyncio.ensure_future(coroutine)
        self._tasks.add(task)

        def finished(done):
            self._tasks.discard(done)
            if done.cancelled() or self._destroyed:
                return
            error = done.exception()
            if error is not None:
                self._error = str(error)
            self.refresh()

        task.add_done_callback(finished)

    def _invoke(self, name, *args):
        callback = self._callbacks[name]
        if callback:
            self._call(callback, *args)

    async def _capture(self):
        issue_id = self._selected().id
        stage = self.service.stage
        result = self._callbacks["capture"](issue_id)
        viewpoint = await result if inspect.isawaitable(result) else result
        if stage is self.service.stage and issue_id == self.selected_issue_id and not self._destroyed:
            self.pending_viewpoint = viewpoint

    async def _annotate(self, viewpoint_id):
        issue_id = self._selected().id
        stage = self.service.stage
        result = self._callbacks["markup"](viewpoint_id)
        viewpoint = await result if inspect.isawaitable(result) else result
        if (stage is self.service.stage and issue_id == self.selected_issue_id
                and not self._destroyed and self.pending_viewpoint
                and self.pending_viewpoint.id == viewpoint_id and viewpoint):
            self.pending_viewpoint = viewpoint
        if stage is self.service.stage and issue_id == self.selected_issue_id:
            self._shown_content = None

    def _set_author(self):
        self.service.author_name = self.author.as_string

    def _remove_related(self, element):
        record = self._selected()
        self.service.set_related_elements(record.id, tuple(ref for ref in record.related_elements if ref != element))

    def _open_comment_viewpoint(self, viewpoint_id):
        if not self.service.viewport:
            raise ValueError("The review viewport is unavailable.")
        self.service.viewport.restore(self.service.store.get_viewpoint(viewpoint_id))

    def _snapshot_provider(self, viewpoint_id):
        from io import BytesIO
        from PIL import Image

        snapshot = self.service.store.get_viewpoint(viewpoint_id).snapshot
        if not snapshot:
            return None
        cached = self._image_providers.get(viewpoint_id)
        if cached and cached[0] == snapshot:
            return cached[1]
        with Image.open(BytesIO(snapshot)) as image:
            if image.format not in ("PNG", "JPEG"):
                raise ValueError("This snapshot format cannot be displayed.")
            if max(image.size) > 16384 or image.width * image.height > 64_000_000:
                raise ValueError("This snapshot is too large to display safely.")
            image.thumbnail((1280, 960))
            rgba = image.convert("RGBA")
            provider = cached[1] if cached else ui.ByteImageProvider()
            provider.set_bytes_data(list(rgba.tobytes()), list(rgba.size))
        self._image_providers[viewpoint_id] = (snapshot, provider)
        return provider

    def _show_snapshot(self, viewpoint_id):
        provider = self._snapshot_provider(viewpoint_id)
        if provider is None:
            raise ValueError("This viewpoint has no retained snapshot.")
        window = self._snapshot_windows.get(viewpoint_id)
        if window is None:
            window = ui.Window("Review snapshot", width=900, height=650)
            with window.frame:
                ui.ImageWithProvider(provider, fill_policy=ui.FillPolicy.PRESERVE_ASPECT_FIT)
            self._snapshot_windows[viewpoint_id] = window
        window.visible = True

    def _build_snapshot(self, viewpoint_id):
        try:
            provider = self._snapshot_provider(viewpoint_id)
            if provider is not None:
                ui.Label("Retained snapshot", name="section", height=18)
                ui.ImageWithProvider(provider, height=170, fill_policy=ui.FillPolicy.PRESERVE_ASPECT_FIT)
                ui.Button("Open snapshot", height=27, clicked_fn=lambda: self._call(self._show_snapshot, viewpoint_id))
        except (ValueError, KeyError, OSError) as exc:
            ui.Label(f"Snapshot unavailable: {exc}", name="error", word_wrap=True, height=32)

    def _build(self):
        if self._destroyed:
            return
        has_stage = self.service.stage is not None
        records = self._read_records()
        can_edit = has_stage and not self.load_error
        with ui.ScrollingFrame():
            with ui.VStack(spacing=8, margin=12, height=0):
                with ui.HStack(height=28, spacing=8):
                    ui.Label("ISSUES", style={"font_size": 18})
                    ui.Label(f"{len(records)} records", name="muted", width=90)
                with ui.HStack(height=30, spacing=6):
                    ui.Button("Place pin", name="primary", enabled=can_edit and bool(self._callbacks["place"]),
                              clicked_fn=lambda: self._invoke("place", None), tooltip="Click a model surface to create an issue")
                    ui.Button("Import BCF", enabled=can_edit and bool(self._callbacks["import"]), clicked_fn=lambda: self._invoke("import"))
                    ui.Button("Export BCF", enabled=can_edit and bool(self._callbacks["export"]), clicked_fn=lambda: self._invoke("export"))
                ui.Label("Author name", name="section", height=18)
                with ui.HStack(height=28, spacing=6):
                    ui.StringField(self.author, tooltip="Name attributed to new changes and comments")
                    ui.Button("Apply", width=65, clicked_fn=lambda: self._call(self._set_author))
                ui.Label("Unsaved changes. Use scene Save to persist." if self.service.is_dirty else "Changes persist with scene Save.",
                         name="muted", word_wrap=True, height=32)
                if self._error or self.load_error:
                    ui.Label(self.load_error or self._error, name="error", word_wrap=True, height=36)
                if not has_stage:
                    ui.Label("Open the parent USD scene to review or create issues.", word_wrap=True, height=44)
                    return
                if self.load_error:
                    ui.Label("Issue editing is unavailable until the scene's issue data can be read.", name="muted", word_wrap=True, height=44)
                    return
                ui.Separator(height=1)
                self._build_list()
                ui.Separator(height=1)
                if self.selected_issue_id:
                    self._build_details()
                else:
                    ui.Label("Create an issue", name="section", height=20)
                    ui.Label("Place a pin on a model surface, or create a record without a pin.", name="muted", word_wrap=True, height=38)
                    ui.Label("Description", height=18)
                    ui.StringField(self.description, multiline=True, height=82, tooltip="Describe the model issue")
                    ui.Button("Create record", height=30, clicked_fn=lambda: self._call(self.create_record, self.description.as_string))

    def _build_list(self):
        records = self._read_records()
        ui.Label("PROJECT ISSUE LIST", name="section", height=18)
        with ui.ScrollingFrame(height=160):
            with ui.VStack(spacing=4, height=0):
                if not records:
                    ui.Label("No issues in this scene yet.", name="muted", height=28)
                for record in records:
                    excerpt = " ".join(record.description.split())
                    if len(excerpt) > 42:
                        excerpt = excerpt[:39] + "..."
                    ui.Button(f"{record.status.value} | {excerpt}", height=32,
                              name="selected" if record.id == self.selected_issue_id else "",
                              tooltip=record.description,
                              clicked_fn=lambda issue_id=record.id: self._call(self.select_issue, issue_id))
        if self.selected_issue_id:
            ui.Button("New issue record", height=27, clicked_fn=self._new_record)

    def _new_record(self):
        self.selected_issue_id = None
        self.pending_viewpoint = None
        self._description_record = None
        self.description.set_value("")
        self.comment.set_value("")
        self.refresh()

    def _build_details(self):
        record = self.service.get_issue(self.selected_issue_id)
        ui.Label("Description", name="section", height=18)
        ui.StringField(self.description, multiline=True, height=84, tooltip="Edit the issue description, then Apply")
        ui.Button("Apply description", height=28, clicked_fn=lambda: self._call(self.submit_description, self.description.as_string))
        ui.Label("Status", name="section", height=18)
        statuses = tuple(Status)
        combo = ui.ComboBox(statuses.index(record.status), *(status.value for status in statuses), height=28)
        combo.model.add_item_changed_fn(lambda model, _: self._call(self.change_status, statuses[model.get_item_value_model().as_int]))
        ui.Label(f"Created by {record.author}\n{record.created_at}", name="muted", word_wrap=True, height=36)
        with ui.HStack(height=30, spacing=6):
            ui.Button("Open review view", enabled=bool(record.initial_viewpoint_id), clicked_fn=lambda: self._call(self.service.open_issue, record.id))
            ui.Button("Focus related", enabled=bool(record.related_elements), clicked_fn=lambda: self._call(self.service.focus_related, record.id))
        if record.initial_viewpoint_id:
            self._build_snapshot(record.initial_viewpoint_id)
        self._build_related(record)
        self._build_comments(record)

    def _build_related(self, record):
        ui.Label("Related elements", name="section", height=20)
        if not record.anchor:
            ui.Label("No spatial pin. Attach only after locating the element.", name="muted", word_wrap=True, height=32)
        else:
            ui.Label(f"Pin: {record.anchor.element.prim_path or record.anchor.element.source_id}", name="muted", word_wrap=True, height=30)
            state = attachment_state(self.service.stage, record.anchor)
            if state != "verified":
                message = {"missing": "Pin element is missing. Reattach to recover its location.",
                           "ambiguous": "Pin element matches more than once. Reattach explicitly.",
                           "needs_review": "Element geometry changed. Review and reattach the pin."}[state]
                ui.Label(message, name="error", word_wrap=True, height=36)
        for element in record.related_elements:
            with ui.HStack(height=28, spacing=6):
                state = resolve_element(self.service.stage, element).state
                label = element.prim_path or element.source_id
                if state != "resolved":
                    label = f"{state.capitalize()} | {label}"
                ui.Label(label, elided_text=True, tooltip=label)
                ui.Button("Remove", width=68, clicked_fn=lambda ref=element: self._call(self._remove_related, ref))
        with ui.HStack(height=28, spacing=6):
            ui.Button("Add selected", enabled=bool(self._callbacks["related"]), clicked_fn=lambda: self._invoke("related", record.id))
            ui.Button("Reattach pin", enabled=bool(self._callbacks["place"]), clicked_fn=lambda: self._invoke("place", record.id))

    def _build_comments(self, record):
        ui.Separator(height=1)
        ui.Label(f"Comments ({len(record.comments)})", name="section", height=20)
        for comment in record.comments:
            with ui.VStack(spacing=4, height=0):
                ui.Label(f"{comment.author} | {comment.created_at}", name="muted", height=20, elided_text=True,
                         tooltip=f"{comment.author} | {comment.created_at}")
                ui.Label(comment.text, word_wrap=True, height=0)
                if comment.viewpoint_id:
                    self._build_snapshot(comment.viewpoint_id)
                    with ui.HStack(height=27, spacing=6):
                        ui.Button("Open comment view", clicked_fn=lambda viewpoint_id=comment.viewpoint_id: self._call(self._open_comment_viewpoint, viewpoint_id))
                        ui.Button("Annotate comment", enabled=bool(self._callbacks["markup"]),
                                  clicked_fn=lambda viewpoint_id=comment.viewpoint_id: self._call(self._annotate, viewpoint_id))
                ui.Separator(height=1)
        ui.Label("New comment", height=18)
        ui.StringField(self.comment, multiline=True, height=70, tooltip="Write investigation or resolution evidence")
        if self.pending_viewpoint:
            ui.Label("Viewpoint attached to this draft comment.", name="muted", height=20)
        with ui.HStack(height=28, spacing=6):
            ui.Button("Capture viewpoint", enabled=bool(self._callbacks["capture"]), clicked_fn=lambda: self._call(self._capture))
            viewpoint_id = self.pending_viewpoint.id if self.pending_viewpoint else record.initial_viewpoint_id
            ui.Button("Annotate", enabled=bool(viewpoint_id and self._callbacks["markup"]),
                      clicked_fn=lambda: self._call(self._annotate, viewpoint_id))
        ui.Button("Add comment", name="primary", height=30, clicked_fn=lambda: self._call(self.submit_comment, self.comment.as_string))
