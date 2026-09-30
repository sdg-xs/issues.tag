"""Undo only issue records, preserving unrelated root-layer opinions."""
import omni.kit.commands
from pxr import Sdf, Usd


def copy_issues(layer):
    snapshot = Sdf.Layer.CreateAnonymous()
    if layer.GetPrimAtPath("/Issues"):
        Sdf.CopySpec(layer, "/Issues", snapshot, "/Issues")
    return snapshot


def restore_issues(stage, snapshot):
    root = stage.GetRootLayer()
    with Usd.EditContext(stage, root):
        if root.GetPrimAtPath("/Issues"):
            stage.RemovePrim("/Issues")
        if snapshot.GetPrimAtPath("/Issues"):
            Sdf.CopySpec(snapshot, "/Issues", root, "/Issues")


class UpdateIssuesCommand(omni.kit.commands.Command):
    def __init__(self, stage, operation):
        self._stage = stage
        self._operation = operation
        self._before = copy_issues(stage.GetRootLayer())

    def do(self):
        try:
            with Usd.EditContext(self._stage, self._stage.GetRootLayer()):
                return self._operation()
        except Exception:
            restore_issues(self._stage, self._before)
            raise

    def undo(self):
        restore_issues(self._stage, self._before)


omni.kit.commands.register(UpdateIssuesCommand)
