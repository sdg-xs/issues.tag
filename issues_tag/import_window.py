"""Review imported BCF field conflicts before applying the import plan."""

from io import BytesIO

import omni.ui as ui

from .bcf_coordinates import ViewpointImportOptions
from .bcf_diagnostics import camera_diagnostics
from .styles import STYLE


class ReferenceSelectionWindow:
    def __init__(self, paths, on_select):
        self.paths = tuple(paths)
        self.on_select = on_select
        self._error = ''
        self._destroyed = False
        self.window = ui.Window('BCF reference model', width=680, height=230)
        self.window.frame.style = STYLE
        self.window.frame.set_build_fn(self._build)
        self.window.frame.rebuild()

    def destroy(self):
        if not self._destroyed:
            self._destroyed = True
            self.on_select = None
            self.window.destroy()

    def _select_clicked(self):
        if self._destroyed:
            return
        index = self._reference_model.get_item_value_model().as_int
        if not 1 <= index <= len(self.paths):
            self._error_label.text = 'Choose a reference model before previewing the import.'
            return
        try:
            self.on_select(self.paths[index - 1])
        except Exception as error:
            self._error = str(error)
            self._error_label.text = self._error
            return
        self.destroy()

    def _build(self):
        if self._destroyed:
            return
        with ui.VStack(spacing=8, margin=16):
            ui.Label('Choose the reference model for these BCF viewpoints.', word_wrap=True, height=36)
            self._reference_model = ui.ComboBox(0, 'Choose reference model', *self.paths, height=30).model
            self._error_label = ui.Label(self._error, name='error', word_wrap=True, height=44)
            with ui.HStack(height=32, spacing=8):
                ui.Button('Cancel', clicked_fn=self.destroy)
                ui.Button('Preview import', name='primary', clicked_fn=self._select_clicked)


class ImportWindow:
    def __init__(self, plan, on_apply, on_cancel=None, *, on_replan=None, on_preview=None,
                 on_close_preview=None, reference_paths=()):
        self.plan = plan
        self.on_apply = on_apply
        self.on_cancel = on_cancel
        self.on_replan = on_replan
        self.on_preview = on_preview
        self.on_close_preview = on_close_preview
        self.reference_paths = tuple(reference_paths)
        self.selected_viewpoint_id = plan.document.viewpoints[0].id if plan.document.viewpoints else None
        self._provider = self._snapshot_bytes = None
        self._camera_options_dirty = False
        self._pending_options = None
        self.choices = {conflict.key: "keep_local" for conflict in plan.conflicts}
        self.applied = False
        self._error = ""
        self._summary = ""
        self._destroyed = False
        self.window = ui.Window("BCF import review", width=720, height=820)
        self.window.set_visibility_changed_fn(self._visibility_changed)
        self.window.frame.style = STYLE
        self.window.frame.set_build_fn(self._build)
        self.window.frame.rebuild()

    def show(self):
        self.window.visible = True

    def destroy(self):
        if not self._destroyed:
            self._destroyed = True
            self.window.set_visibility_changed_fn(None)
            try:
                self._close_preview()
            finally:
                self.on_apply = self.on_cancel = self.on_replan = self.on_preview = None
                self.on_close_preview = None
                self._provider = self._snapshot_bytes = None
                self.window.destroy()

    def _visibility_changed(self, visible):
        if not visible:
            self.cancel()

    def _close_preview(self):
        if self.on_close_preview:
            self.on_close_preview()

    def select_viewpoint(self, identity):
        if self._destroyed:
            return
        if identity not in {view.id for view in self.plan.document.viewpoints}:
            raise ValueError('This viewpoint is not part of the import.')
        self._close_preview()
        self.selected_viewpoint_id = identity
        self._camera_options_dirty = False
        self._pending_options = None
        self.window.frame.rebuild()

    def _camera_options_changed(self, model, item):
        if self._destroyed or self.applied:
            return
        self._camera_options_dirty = True
        self._pending_options = ViewpointImportOptions(
            reference_path=self._reference_choices[self._reference_model.get_item_value_model().as_int],
            coordinate_mode=('source_world', 'reference_local')[self._coordinate_model.get_item_value_model().as_int],
            fov_mode=('file', 'horizontal')[self._fov_model.get_item_value_model().as_int])
        self._close_preview()
        self._preview_button.enabled = False
        self._apply_button.enabled = False

    def _require_recalculated(self):
        if self._camera_options_dirty:
            raise ValueError('Recalculate camera before previewing or applying these options.')

    def _replan_clicked(self):
        if self._destroyed or self.applied or not self.on_replan:
            return
        try:
            options = dict(self.plan.viewpoint_options_signatures)
            options[self.selected_viewpoint_id] = self._pending_options or ViewpointImportOptions(
                reference_path=self._reference_choices[self._reference_model.get_item_value_model().as_int],
                coordinate_mode=('source_world', 'reference_local')[self._coordinate_model.get_item_value_model().as_int],
                fov_mode=('file', 'horizontal')[self._fov_model.get_item_value_model().as_int])
            plan = self.on_replan(options)
            self._close_preview()
            self.choices = {conflict.key: self.choices.get(conflict.key, 'keep_local') for conflict in plan.conflicts}
            self.plan = plan
            self._camera_options_dirty = False
            self._pending_options = None
            self._error = ''
        except Exception as error:
            self._error = str(error)
        self.window.frame.rebuild()

    def _preview_clicked(self):
        if self._destroyed or self.applied or not self.on_preview:
            return
        try:
            self._require_recalculated()
            view = next(view for view in self.plan.document.viewpoints if view.id == self.selected_viewpoint_id)
            self.on_preview(view)
            self._error = ''
        except Exception as error:
            self._error = str(error)
        self.window.frame.rebuild()

    def set_choice(self, key, choice):
        if key not in self.choices:
            raise ValueError("This field is not part of the import preview.")
        if choice not in ("keep_local", "use_imported"):
            raise ValueError("Choose Keep local or Use imported.")
        if self.applied:
            raise ValueError("This import has already been applied.")
        self.choices[key] = choice

    def apply_choices(self):
        if self._destroyed:
            raise ValueError('This import review has closed.')
        if self.applied:
            raise ValueError("This import has already been applied.")
        self._require_recalculated()
        self._close_preview()
        result = self.on_apply(dict(self.choices))
        self.applied = True
        self._summary = (f"Imported {result.created} new issues and updated {result.updated}."
                         if result is not None else "Import applied.")
        if result is not None and result.viewpoints_updated:
            self._summary += f" Remapped {result.viewpoints_updated} existing viewpoints."
        self.window.frame.rebuild()
        return result

    def cancel(self):
        if self._destroyed:
            return
        try:
            if self.on_cancel:
                self.on_cancel()
        finally:
            self.destroy()

    def _apply_clicked(self):
        if self._destroyed:
            return
        try:
            self.apply_choices()
            self._error = ""
        except Exception as exc:
            self._error = str(exc)
        self.window.frame.rebuild()

    def _camera_review(self):
        source = self.plan.source_document or self.plan.document
        rows = camera_diagnostics(source, self.plan.document)
        if not rows:
            return
        identities = [row['viewpoint_id'] for row in rows]
        index = identities.index(self.selected_viewpoint_id)
        row = rows[index]
        model = ui.ComboBox(index, *[f"{', '.join(r['topic_ids'])} / {r['viewpoint_id']}" for r in rows], height=30).model
        model.add_item_changed_fn(lambda model, _: self.select_viewpoint(identities[model.get_item_value_model().as_int]))
        ui.Label(f"Topic: {', '.join(row['topic_ids'])}\nViewpoint: {row['viewpoint_id']}", height=44, word_wrap=True)
        original = next(view for view in source.viewpoints if view.id == self.selected_viewpoint_id)
        self._snapshot(original)
        ui.Label(f"Original position: {row['source_position']}\nConverted position: {row['converted_position']}", height=44, word_wrap=True)
        ui.Label(f"Projection: {row['projection'] or 'No camera'} | BCF {row['source_version'] or 'Native'}", height=22)
        coordinate = {'source_world': 'Source world', 'reference_local': 'Relative to reference', 'native': 'Native recorded frame'}
        fov = {'file': 'File interpretation', 'horizontal': 'Horizontal FOV (BCF 2.1)', 'native': 'Native recorded frame'}
        ui.Label(f"Reference: {row['reference_path'] or 'Scene coordinates'}\n{coordinate[row['coordinate_mode']]} | {fov[row['fov_mode']]}", height=44, word_wrap=True)
        enabled = bool(self.on_replan) and not self.applied and bool(original.camera) and original.id not in source.native_viewpoints
        option = self._pending_options or dict(self.plan.viewpoint_options_signatures).get(original.id, ViewpointImportOptions())
        self._reference_choices = (None, *dict.fromkeys((*self.reference_paths, *([option.reference_path] if option.reference_path else []))))
        self._reference_model = ui.ComboBox(self._reference_choices.index(option.reference_path),
            'Import reference / scene', *self._reference_choices[1:], enabled=enabled, height=30).model
        self._coordinate_model = ui.ComboBox(int(option.coordinate_mode == 'reference_local'),
            'Source world', 'Relative to reference', enabled=enabled, height=30).model
        horizontal = row['source_version'] == '2.1' and row['projection'] == 'perspective'
        self._fov_model = ui.ComboBox(int(option.fov_mode == 'horizontal'),
            'File interpretation', 'Horizontal FOV (BCF 2.1)', enabled=enabled and horizontal, height=30).model
        with ui.HStack(height=32, spacing=8):
            ui.Button('Recalculate camera', enabled=enabled, clicked_fn=self._replan_clicked)
            self._preview_button = ui.Button('Preview camera', enabled=bool(self.on_preview) and bool(original.camera) and not self.applied and not self._camera_options_dirty,
                      clicked_fn=self._preview_clicked)
        for model in (self._reference_model, self._coordinate_model, self._fov_model):
            model.add_item_changed_fn(self._camera_options_changed)
        ui.Label('Choose options, then Recalculate camera before previewing or applying.', name='muted', word_wrap=True, height=30)
        ui.Label('Camera only: visibility and clipping are unchanged.', name='muted', word_wrap=True, height=30)

    def _snapshot(self, record):
        if not record.snapshot:
            self._provider = self._snapshot_bytes = None
            ui.Label('No screenshot saved.', name='muted', height=25)
            return
        try:
            if record.snapshot != self._snapshot_bytes:
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
        except (ValueError, OSError) as error:
            ui.Label(str(error), name='error', word_wrap=True, height=30)

    def _build(self):
        if self._destroyed:
            return
        with ui.ScrollingFrame():
            with ui.VStack(spacing=8, margin=16, height=0):
                ui.Label("REVIEW BCF IMPORT", height=28, style={"font_size": 18})
                ui.Label(f"{len(self.plan.document.issues)} issues | {len(self.plan.conflicts)} field conflicts", height=22, name="muted")
                ui.Label("Review conflicting fields before applying. Existing values are kept unless you choose Use imported.",
                         name="muted", word_wrap=True, height=42)
                if self.plan.frame_signature:
                    ui.Label('Existing imported viewpoints are remapped if their reference frame changes.',
                             name='muted', word_wrap=True, height=36)
                for warning in self.plan.document.warnings:
                    ui.Label(str(warning), name="muted", word_wrap=True, height=40)
                if self._error:
                    ui.Label(self._error, name="error", word_wrap=True, height=44)
                if self._summary:
                    ui.Label(self._summary, height=36, word_wrap=True)
                self._camera_review()
                if not self.plan.conflicts:
                    ui.Label("No conflicting description or status changes.", height=28)
                for conflict in self.plan.conflicts:
                    ui.Separator(height=1)
                    ui.Label(conflict.field.replace("_", " ").capitalize(), height=22)
                    ui.Label(f"Issue {conflict.topic_id}", name="muted", height=20, elided_text=True, tooltip=conflict.topic_id)
                    ui.Label("Local value", name="section", height=18)
                    ui.Label(str(conflict.local), word_wrap=True, height=0)
                    ui.Label("Imported value", name="section", height=18)
                    ui.Label(str(conflict.incoming), word_wrap=True, height=0)
                    model = ui.ComboBox(0 if self.choices[conflict.key] == "keep_local" else 1,
                                        "Keep local", "Use imported", enabled=not self.applied, height=30).model
                    model.add_item_changed_fn(lambda model, _, key=conflict.key:
                                              self.set_choice(key, "keep_local" if model.get_item_value_model().as_int == 0 else "use_imported"))
                ui.Separator(height=1)
                with ui.HStack(height=32, spacing=8):
                    ui.Button("Close" if self.applied else "Cancel", clicked_fn=self.cancel)
                    self._apply_button = ui.Button("Apply import", name="primary", enabled=not self.applied and not self._camera_options_dirty, clicked_fn=self._apply_clicked)
