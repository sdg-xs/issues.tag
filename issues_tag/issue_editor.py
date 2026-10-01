"""Resolve staged changes before closing details or switching issues."""
import asyncio
import omni.ui as ui


class DirtyDetailsDialog:
    def __init__(self):
        self._destroyed = False
        self._result = asyncio.get_running_loop().create_future()
        self.window = ui.Window('Unsaved issue changes', width=390, height=145)
        self.window.set_visibility_changed_fn(lambda visible: self.choose('stay') if not visible else None)
        with self.window.frame:
            with ui.VStack(spacing=12, margin=16):
                ui.Label('Save changes to this issue?', height=30)
                with ui.HStack(spacing=8, height=32):
                    for label, decision in (('Save', 'save'), ('Discard', 'discard'), ('Stay', 'stay')):
                        ui.Button(label, clicked_fn=lambda value=decision: self.choose(value))

    def choose(self, decision):
        if not self._destroyed and not self._result.done():
            self._result.set_result(decision)

    async def wait(self):
        return await asyncio.shield(self._result)

    def destroy(self):
        if self._destroyed:
            return
        self.choose('stay')
        self._destroyed = True
        window, self.window = self.window, None
        try:
            window.set_visibility_changed_fn(None)
        finally:
            window.destroy()
