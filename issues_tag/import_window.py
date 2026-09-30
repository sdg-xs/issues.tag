"""Review imported BCF field conflicts before applying the import plan."""

import omni.ui as ui

from .styles import STYLE


class ImportWindow:
    def __init__(self, plan, on_apply, on_cancel=None):
        self.plan = plan
        self.on_apply = on_apply
        self.on_cancel = on_cancel
        self.choices = {conflict.key: "keep_local" for conflict in plan.conflicts}
        self.applied = False
        self._error = ""
        self._summary = ""
        self._destroyed = False
        self.window = ui.Window("BCF import review", width=540, height=640)
        self.window.frame.style = STYLE
        self.window.frame.set_build_fn(self._build)
        self.window.frame.rebuild()

    def show(self):
        self.window.visible = True

    def destroy(self):
        if not self._destroyed:
            self._destroyed = True
            self.window.destroy()

    def set_choice(self, key, choice):
        if key not in self.choices:
            raise ValueError("This field is not part of the import preview.")
        if choice not in ("keep_local", "use_imported"):
            raise ValueError("Choose Keep local or Use imported.")
        if self.applied:
            raise ValueError("This import has already been applied.")
        self.choices[key] = choice

    def apply_choices(self):
        if self.applied:
            raise ValueError("This import has already been applied.")
        result = self.on_apply(dict(self.choices))
        self.applied = True
        self._summary = (f"Imported {result.created} new issues and updated {result.updated}."
                         if result is not None else "Import applied.")
        self.window.frame.rebuild()
        return result

    def cancel(self):
        if self.on_cancel:
            self.on_cancel()
        self.destroy()

    def _apply_clicked(self):
        try:
            self.apply_choices()
            self._error = ""
        except Exception as exc:
            self._error = str(exc)
        self.window.frame.rebuild()

    def _build(self):
        if self._destroyed:
            return
        with ui.ScrollingFrame():
            with ui.VStack(spacing=8, margin=16, height=0):
                ui.Label("REVIEW BCF IMPORT", height=28, style={"font_size": 18})
                ui.Label(f"{len(self.plan.document.issues)} issues | {len(self.plan.conflicts)} field conflicts", height=22, name="muted")
                ui.Label("Review conflicting fields before applying. Existing values are kept unless you choose Use imported.",
                         name="muted", word_wrap=True, height=42)
                for warning in self.plan.document.warnings:
                    ui.Label(str(warning), name="muted", word_wrap=True, height=40)
                if self._error:
                    ui.Label(self._error, name="error", word_wrap=True, height=44)
                if self._summary:
                    ui.Label(self._summary, height=36, word_wrap=True)
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
                    ui.Button("Apply import", name="primary", enabled=not self.applied, clicked_fn=self._apply_clicked)
