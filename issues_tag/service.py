"""Scene-scoped issue actions and notifications."""
import omni.usd


class IssueService:
    def __init__(self):
        self._context = omni.usd.get_context()

    @property
    def stage(self):
        return self._context.get_stage()

    def destroy(self):
        self._context = None
