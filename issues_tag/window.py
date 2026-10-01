"""Separate dockable issue list and staged details panels."""
from io import BytesIO
import omni.kit.app
import omni.ui as ui
from .model import Status
from .elements import attachment_state, resolve_element
from .styles import STYLE


def _dock_when_ready(owner, side, ratio):
    if owner._dock_subscription is not None or owner.window.docked:
        return
    window = owner.window

    def on_update(event):
        if owner._destroyed or owner.window is not window or owner._dock_subscription is None:
            return
        # Native windows acquire their geometry after the first UI update.
        # Capture may hide a new panel meanwhile; leave that request pending.
        if not window.visible or window.frame.computed_width <= 0 or window.frame.computed_height <= 0:
            return
        viewport = ui.Workspace.get_window('Viewport')
        if viewport is None:
            return
        owner._dock_subscription = None
        if not window.docked:
            window.dock_in(viewport, side, ratio)

    owner._dock_subscription = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(
        on_update, name='issues.panel_docking')


class IssuesWindow:
    def __init__(self, service, *, on_select, on_create, on_import=None, on_export=None, on_error=None):
        self.service = service
        self.on_select, self.on_create = on_select, on_create
        self.on_import, self.on_export, self.on_error = on_import, on_export, on_error
        self.selected_issue_id = None
        self.search = ui.SimpleStringModel('')
        self._author_name = service.author_name
        self.author = ui.SimpleStringModel(self._author_name)
        self.status_filter = 'All statuses'
        self.type_filter = 'All types'
        self.records, self.types = (), ()
        self.load_error = ''
        self._error = ''
        self._placing = False
        self._on_cancel_placement = None
        self._stage = service.stage
        self._signature = None
        self._destroyed = False
        self._dock_subscription = None
        self.window = ui.Window('Issues', width=330, height=660)
        self.window.frame.style = STYLE
        self.window.frame.set_build_fn(self._build)
        self._search_listener = self.search.add_value_changed_fn(lambda model: self.refresh())
        service.add_listener(self.refresh)
        self.refresh()

    def _call(self, callback, *args):
        if self._destroyed or callback is None:
            return
        try:
            if self.on_error:
                return self.on_error(callback, *args)
            return callback(*args)
        except Exception as exc:
            self._error = str(exc)
            self.refresh()

    def show(self):
        if self._destroyed:
            return
        self.window.visible = True
        self._signature = None
        self.refresh()
        _dock_when_ready(self, ui.DockPosition.LEFT, 0.23)

    def select_issue(self, issue_id):
        if not self._destroyed:
            self._call(self.on_select, issue_id)

    def filtered_records(self):
        if self._destroyed or self.service.stage is None:
            return ()
        text = self.search.as_string.strip().casefold()
        return tuple(sorted((r for r in self.service.list_issues()
            if (self.status_filter == 'All statuses' or r.status.value == self.status_filter)
            and (self.type_filter == 'All types' or r.issue_type == self.type_filter)
            and (not text or text in f'{r.number} {r.title} {r.description}'.casefold())),
            key=lambda r: (r.number, r.id)))

    @property
    def visible_issue_ids(self):
        return frozenset(r.id for r in self.records)

    def clear_filters(self):
        if self._destroyed:
            return
        self.status_filter, self.type_filter = 'All statuses', 'All types'
        self.search.set_value('')
        self.refresh()

    def _create(self):
        if not self._destroyed and not self._placing and self.service.stage is not None and not self.load_error:
            self._call(self.on_create)

    def set_placement_state(self, active, on_cancel=None):
        if self._destroyed:
            return
        self._placing = bool(active)
        self._on_cancel_placement = on_cancel if active else None
        self.refresh()

    def _cancel_placement(self):
        if not self._destroyed and self._placing:
            self._call(self._on_cancel_placement)

    def _set_author(self):
        self.service.author_name = self.author.as_string
        self.author.set_value(self.service.author_name)
        self._error = ''
        self.refresh()

    def _filter(self, model, values, attribute):
        if self._destroyed:
            return
        setattr(self, attribute, values[model.get_item_value_model().as_int])
        self.refresh()

    def refresh(self, *args):
        if self._destroyed:
            return
        author_name = self.service.author_name
        if author_name != self._author_name:
            if self.author.as_string == self._author_name:
                self.author.set_value(author_name)
            self._author_name = author_name
        if self._stage is not self.service.stage:
            self._stage = self.service.stage
            self.selected_issue_id = None
            self._error = ''
        try:
            types = self.service.list_types() if self.service.stage is not None else ('Default',)
            if self.type_filter not in ('All types', *types):
                self.type_filter = 'All types'
            records = self.filtered_records()
            error = ''
        except ValueError as exc:
            records, types, error = (), ('Default',), str(exc)
            if self.type_filter not in ('All types', *types):
                self.type_filter = 'All types'
        viewport = self.service.viewport
        if viewport:
            viewport.filtered_issue_ids = frozenset(r.id for r in records)
        self.records, self.types, self.load_error = records, types, error
        signature = (self.service.stage, records, types, self.selected_issue_id,
                     self.status_filter, self.type_filter, error, self._error, self.service.is_dirty, self._placing,
                     self._author_name)
        if signature != self._signature:
            if not self.window.visible:
                return
            self._signature = signature
            self.window.frame.rebuild()

    def _build(self):
        if self._destroyed:
            return
        can_edit = self.service.stage is not None and not self.load_error
        with ui.VStack(spacing=8, margin=12):
            with ui.HStack(height=28):
                ui.Label('ISSUES', name='heading')
                ui.Label(str(len(self.records)), width=35, name='muted')
            ui.Button('Create issue', name='primary', height=30, clicked_fn=self._create, enabled=can_edit and not self._placing)
            if self._placing:
                ui.Label('Click a model surface to place the issue pin.', name='muted', word_wrap=True, height=38)
                ui.Button('Cancel placement', height=28, clicked_fn=self._cancel_placement,
                          enabled=bool(self._on_cancel_placement))
            ui.Label('Search', name='section', height=18)
            ui.StringField(self.search, height=28, tooltip='Search issue number, title or description')
            with ui.HStack(height=18, spacing=6):
                ui.Label('Status', name='section')
                ui.Label('Type', name='section')
            with ui.HStack(height=28, spacing=6):
                statuses = ('All statuses', *(s.value for s in Status))
                types = ('All types', *self.types)
                status = ui.ComboBox(statuses.index(self.status_filter), *statuses)
                status.model.add_item_changed_fn(lambda model, item: self._filter(model, statuses, 'status_filter'))
                type_box = ui.ComboBox(types.index(self.type_filter), *types)
                type_box.model.add_item_changed_fn(lambda model, item: self._filter(model, types, 'type_filter'))
            with ui.ScrollingFrame():
                with ui.VStack(spacing=6, height=0):
                    if self.load_error or self._error:
                        ui.Label(self.load_error or self._error, name='error', word_wrap=True, height=40)
                    elif self.service.stage is None:
                        ui.Label('Open the parent USD scene to review or create issues.', name='muted', word_wrap=True, height=45)
                    elif not self.records:
                        ui.Label('No issues match these filters.', name='muted', height=35)
                    for record in self.records:
                        ui.Button(f'#{record.number}  {record.title}\n{record.status.value}  |  {record.issue_type}',
                            name='selected' if record.id == self.selected_issue_id else '', height=55,
                            tooltip=record.description, clicked_fn=lambda issue_id=record.id: self.select_issue(issue_id))
            ui.Label('Author name', name='section', height=18)
            with ui.HStack(height=28, spacing=6):
                ui.StringField(self.author, tooltip='Name attributed to new changes and comments')
                ui.Button('Apply', width=65, clicked_fn=lambda: self._call(self._set_author))
            ui.Label(f'Current author: {self._author_name}', name='muted', word_wrap=True, height=30)
            ui.Label('Unsaved scene changes. Use scene Save.' if self.service.is_dirty else 'Save issue edits first, then save scene.',
                     name='muted', word_wrap=True, height=30)
            with ui.HStack(height=28, spacing=6):
                ui.Button('Import BCF', enabled=can_edit and bool(self.on_import), clicked_fn=lambda: self._call(self.on_import))
                ui.Button('Export BCF', enabled=can_edit and bool(self.on_export), clicked_fn=lambda: self._call(self.on_export))

    def destroy(self):
        if self._destroyed:
            return
        self._destroyed = True
        self._dock_subscription = None
        service, self.service = self.service, None
        window, self.window = self.window, None
        self.on_select = self.on_create = self.on_import = self.on_export = self.on_error = None
        self._on_cancel_placement = None
        self._placing = False
        self._stage = self._signature = None
        self.records, self.types = (), ()
        errors = []
        actions = (lambda: service.remove_listener(self.refresh),
                   lambda: self.search.remove_value_changed_fn(self._search_listener),
                   lambda: setattr(service.viewport, 'filtered_issue_ids', None) if service.viewport else None,
                   window.destroy)
        for action in actions:
            try:
                action()
            except Exception as exc:
                errors.append(exc)
        if errors:
            raise ExceptionGroup('Issue list cleanup failed', errors)


class IssueDetailsWindow:
    def __init__(self, session, types, *, on_save, on_cancel, on_annotate, on_replace, on_comment_view,
                 on_reattach=None, on_add_related=None, on_remove_related=None, on_focus_related=None,
                 on_capture_comment=None, on_annotate_comment=None, on_add_comment=None, on_open_review_view=None):
        self.session, self.types = session, types
        self.on_save, self.on_cancel = on_save, on_cancel
        self.on_open_review_view = on_open_review_view
        self._draft_state = None
        self.on_annotate, self.on_replace, self.on_comment_view = on_annotate, on_replace, on_comment_view
        self.on_reattach, self.on_add_related = on_reattach, on_add_related
        self.on_remove_related, self.on_focus_related = on_remove_related, on_focus_related
        self.on_capture_comment, self.on_annotate_comment, self.on_add_comment = on_capture_comment, on_annotate_comment, on_add_comment
        self.title = ui.SimpleStringModel(session.record.title)
        self.description = ui.SimpleStringModel(session.record.description)
        self.comment = ui.SimpleStringModel(session.comment_text)
        self._issue_type = session.record.issue_type
        self._destroyed = False
        self._dock_subscription = None
        self._provider = None
        self._snapshot_bytes = None
        self._comment_previews = {}
        self._error = ''
        self.busy = False
        self.window = ui.Window('Issue details', width=370, height=720)
        self.window.frame.style = STYLE
        self.window.frame.set_build_fn(self._build)
        self.window.set_visibility_changed_fn(self._visibility)
        self._model_listeners = tuple((model, model.add_value_changed_fn(lambda model: self.sync()))
                                      for model in (self.title, self.description, self.comment))
        self.window.frame.rebuild()
        _dock_when_ready(self, ui.DockPosition.RIGHT, 0.26)

    def _visibility(self, visible):
        if not visible and not self._destroyed:
            self.window.visible = True
            self._action(self.on_cancel, allow_busy=True)

    def sync(self):
        if self._destroyed or self.busy:
            return
        self.session.update(title=self.title.as_string, description=self.description.as_string,
                            issue_type=self._issue_type)
        self.session.comment_text = self.comment.as_string
        self._update_draft_state()

    def _update_draft_state(self):
        if self._draft_state is not None:
            self._draft_state.text = ('Unsaved issue edits. Save issue, then save scene.' if self.session.dirty
                                      else 'No unsaved issue edits. Scene Save writes committed changes to disk.')

    def _action(self, callback, *args, allow_busy=False):
        if self._destroyed or (self.busy and not allow_busy) or callback is None:
            return
        try:
            self.sync()
            return callback(*args)
        except Exception as exc:
            self.set_error(str(exc))

    def set_error(self, message):
        if self._destroyed:
            return
        self._error = message
        self.refresh()

    def set_busy(self, busy):
        if self._destroyed:
            return
        self.busy = busy
        self.refresh()

    def refresh(self):
        if not self._destroyed and self.window.visible:
            self.window.frame.rebuild()

    def show(self):
        if not self._destroyed:
            self.window.visible = True
            self.refresh()

    def _pick(self, model, values, field):
        if self._destroyed or self.busy:
            return
        value = values[model.get_item_value_model().as_int]
        if field == 'issue_type':
            self._issue_type = value
        self.session.update(**{field: value})
        self._update_draft_state()

    def clear_comment(self):
        if not self._destroyed:
            self.comment.set_value('')
            self.refresh()

    def _build_related(self, record):
        ui.Label('Attachment', name='section', height=18)
        if record.anchor:
            ui.Label(record.anchor.element.prim_path or record.anchor.element.source_id,
                     name='muted', word_wrap=True, height=30)
            state = attachment_state(self.session.stage, record.anchor)
            if state != 'verified':
                message = {'missing': 'Pin element is missing. Reattach to locate it.',
                           'ambiguous': 'Pin matches multiple elements. Reattach explicitly.',
                           'needs_review': 'Element geometry changed. Review and reattach the pin.'}
                ui.Label(message.get(state, state), name='error', word_wrap=True, height=36)
        else:
            ui.Label('No spatial pin. Locate the element, then attach it.', name='muted', word_wrap=True, height=32)
        ui.Button('Reattach pin', height=28, clicked_fn=lambda: self._action(self.on_reattach),
                  enabled=not self.busy and bool(self.on_reattach))
        ui.Label('Related elements', name='section', height=18)
        for element in record.related_elements:
            state = resolve_element(self.session.stage, element).state
            label = element.prim_path or element.source_id
            if state != 'resolved':
                label = f'{state.capitalize()} | {label}'
            with ui.HStack(height=28, spacing=6):
                ui.Label(label, elided_text=True, tooltip=label)
                ui.Button('Remove', width=68, enabled=not self.busy and bool(self.on_remove_related),
                          clicked_fn=lambda ref=element: self._action(self.on_remove_related, ref))
        with ui.HStack(height=28, spacing=6):
            ui.Button('Add selected', enabled=not self.busy and bool(self.on_add_related),
                      clicked_fn=lambda: self._action(self.on_add_related))
            ui.Button('Focus related', enabled=not self.busy and bool(record.related_elements) and bool(self.on_focus_related),
                      clicked_fn=lambda: self._action(self.on_focus_related))

    def _snapshot(self, record):
        if not record or not record.snapshot:
            self._provider, self._snapshot_bytes = None, None
            ui.Label('No screenshot saved.', name='muted', height=25)
            return
        if self._snapshot_bytes != record.snapshot:
            from PIL import Image

            with Image.open(BytesIO(record.snapshot)) as image:
                if image.format not in ('PNG', 'JPEG'):
                    raise ValueError('This screenshot format cannot be displayed.')
                if max(image.size) > 16384 or image.width * image.height > 64000000:
                    raise ValueError('Screenshot is too large to display.')
                image.thumbnail((1280, 960))
                rgba = image.convert('RGBA')
                provider = ui.ByteImageProvider()
                provider.set_bytes_data(list(rgba.tobytes()), list(rgba.size))
            self._provider, self._snapshot_bytes = provider, record.snapshot
        ui.ImageWithProvider(self._provider, height=180, fill_policy=ui.IwpFillPolicy.IWP_PRESERVE_ASPECT_FIT)

    def _comment_snapshot(self, record):
        if not record:
            return
        main = self._provider, self._snapshot_bytes
        self._provider, self._snapshot_bytes = self._comment_previews.get(record.id, (None, None))
        try:
            self._snapshot(record)
            self._comment_previews[record.id] = self._provider, self._snapshot_bytes
        except (ValueError, OSError) as exc:
            ui.Label(str(exc), name='error', word_wrap=True)
        finally:
            self._provider, self._snapshot_bytes = main

    def _build(self):
        if self._destroyed:
            return
        record = self.session.record
        views = (*self.session.comment_viewpoints.values(), self.session.comment_viewpoint)
        active_ids = {view.id for view in views if view}
        self._comment_previews = {view_id: preview for view_id, preview in self._comment_previews.items() if view_id in active_ids}
        with ui.VStack(spacing=8, margin=12):
            ui.Label('NEW ISSUE' if self.session.is_new else f'ISSUE #{record.number}', name='heading', height=28)
            ui.Button('Open review view', height=28,
                      clicked_fn=lambda: self._action(self.on_open_review_view),
                      enabled=not self.busy and self.session.viewpoint is not None and bool(self.on_open_review_view))
            with ui.ScrollingFrame():
                with ui.VStack(spacing=8, height=0):
                    ui.Label('Title *', name='section', height=18)
                    ui.StringField(self.title, height=30, enabled=not self.busy)
                    with ui.HStack(height=18, spacing=8):
                        ui.Label('Status', name='section')
                        ui.Label('Type', name='section')
                    with ui.HStack(height=28, spacing=8):
                        statuses = tuple(Status)
                        status = ui.ComboBox(statuses.index(record.status), *(s.value for s in statuses), enabled=not self.busy)
                        status.model.add_item_changed_fn(lambda model, item: self._pick(model, statuses, 'status'))
                        types = tuple(dict.fromkeys((*self.types, self._issue_type)))
                        type_box = ui.ComboBox(types.index(self._issue_type), *types, enabled=not self.busy)
                        type_box.model.add_item_changed_fn(lambda model, item: self._pick(model, types, 'issue_type'))
                    ui.Label('Description', name='section', height=18)
                    ui.StringField(self.description, multiline=True, height=100, enabled=not self.busy)
                    ui.Label('Screenshot', name='section', height=18)
                    try:
                        self._snapshot(self.session.viewpoint)
                    except (ValueError, OSError) as exc:
                        ui.Label(str(exc), name='error', word_wrap=True)
                    with ui.HStack(height=30, spacing=6):
                        ui.Button('Annotate screenshot', clicked_fn=lambda: self._action(self.on_annotate),
                                  enabled=not self.busy and self.session.viewpoint is not None and bool(self.on_annotate))
                        ui.Button('Replace screenshot', clicked_fn=lambda: self._action(self.on_replace),
                                  enabled=not self.busy and bool(self.on_replace))
                    ui.Separator(height=8)
                    ui.Label(f'Created by {record.author}', name='muted', height=20)
                    ui.Label(record.created_at, name='muted', height=20)
                    self._build_related(record)
                    ui.Label(f'Comments ({len(record.comments)})', name='section', height=18)
                    for comment in record.comments:
                        ui.Label(f'{comment.author}  |  {comment.created_at}', name='muted', height=20)
                        ui.Label(comment.text, word_wrap=True, height=0)
                        if comment.viewpoint_id:
                            self._comment_snapshot(self.session.comment_viewpoints.get(comment.id))
                            with ui.HStack(height=28, spacing=6):
                                ui.Button('Open comment view',
                                          clicked_fn=lambda view_id=comment.viewpoint_id: self._action(self.on_comment_view, view_id),
                                          enabled=not self.busy and bool(self.on_comment_view))
                                ui.Button('Annotate comment',
                                          clicked_fn=lambda comment_id=comment.id: self._action(self.on_annotate_comment, comment_id),
                                          enabled=not self.busy and bool(self.on_annotate_comment))
                    ui.Label('New comment', name='section', height=18)
                    ui.StringField(self.comment, multiline=True, height=60, tooltip='Comment to add when saving', enabled=not self.busy)
                    if self.session.comment_viewpoint:
                        self._comment_snapshot(self.session.comment_viewpoint)
                        ui.Label('Viewpoint attached to this draft comment.', name='muted', height=22)
                    with ui.HStack(height=28, spacing=6):
                        ui.Button('Capture viewpoint', enabled=not self.busy and bool(self.on_capture_comment),
                                  clicked_fn=lambda: self._action(self.on_capture_comment))
                        ui.Button('Annotate viewpoint',
                                  enabled=not self.busy and self.session.comment_viewpoint is not None and bool(self.on_annotate_comment),
                                  clicked_fn=lambda: self._action(self.on_annotate_comment))
                    ui.Button('Add comment', height=28, enabled=not self.busy and bool(self.on_add_comment),
                              clicked_fn=lambda: self._action(self.on_add_comment))
                    ui.Label('Comment and attachment changes are saved with the issue.', name='muted', word_wrap=True, height=30)
            if self._error:
                ui.Label(self._error, name='error', word_wrap=True, height=40)
            if self.busy:
                ui.Label('Preparing evidence...', name='muted', height=24)
            self._draft_state = ui.Label('', name='muted', word_wrap=True, height=38)
            self._update_draft_state()
            with ui.HStack(height=32, spacing=6):
                ui.Button('Save', name='primary', clicked_fn=lambda: self._action(self.on_save), enabled=not self.busy)
                ui.Button('Cancel', clicked_fn=lambda: self._action(self.on_cancel, allow_busy=True))

    def destroy(self):
        if self._destroyed:
            return
        self._destroyed = True
        self._dock_subscription = None
        window, self.window = self.window, None
        self.session = None
        self._draft_state = None
        self.on_open_review_view = None
        self.on_save = self.on_cancel = self.on_annotate = self.on_replace = self.on_comment_view = None
        self.on_reattach = self.on_add_related = self.on_remove_related = self.on_focus_related = None
        self.on_capture_comment = self.on_annotate_comment = self.on_add_comment = None
        errors = []
        actions = [lambda: window.set_visibility_changed_fn(None)]
        actions.extend(lambda model=model, listener=listener: model.remove_value_changed_fn(listener)
                       for model, listener in self._model_listeners)
        actions.append(window.destroy)
        for action in actions:
            try:
                action()
            except Exception as exc:
                errors.append(exc)
        self._model_listeners = ()
        self._provider, self._snapshot_bytes = None, None
        self._comment_previews.clear()
        if errors:
            raise ExceptionGroup('Issue details cleanup failed', errors)
