"""Copy annotation specs into draft evidence without changing saved native prims."""
import importlib
import sys
import types
import unittest
from dataclasses import replace
from unittest.mock import patch
from uuid import uuid4
from test_acc_persistence import persistence_sdk, Sdf, Usd


class CopyEvidenceTests(unittest.IsolatedAsyncioTestCase):
    async def exercise(self, fail=False, stale=False):
        with persistence_sdk() as sdk:
            app = types.ModuleType('omni.kit.app')
            with patch.dict(sys.modules, {'omni.kit.app': app}):
                product = importlib.import_module(sdk.package + '.markup')
                adapter = product.MarkupAdapter(sdk.service)
                stage = sdk.service.stage
                saved_path = '/Viewport_Markups/Saved'
                stage.DefinePrim(saved_path, 'Scope')
                annotation = stage.DefinePrim(saved_path + '/Arrow', 'Scope')
                annotation.CreateAttribute('color', Sdf.ValueTypeNames.String).Set('red')
                product.UsdGeom.Camera.Define(stage, saved_path + '/Camera')
                view = sdk.model.ViewpointRecord(str(uuid4()), snapshot=b'saved PNG', markup_path=saved_path)
                original = stage.GetRootLayer().ExportToString()
                draft_path = '/Viewport_Markups/IssueEvidence_copy'
                async def capture():
                    with Usd.EditContext(stage, stage.GetRootLayer()):
                        stage.DefinePrim(draft_path, 'Scope')
                        product.UsdGeom.Camera.Define(stage, draft_path + '/Camera').GetFocalLengthAttr().Set(71)
                    if stale: sdk.service.generation += 1
                    return replace(view, id=str(uuid4()), markup_path=draft_path, snapshot=b'draft PNG')
                adapter.capture_viewpoint = capture
                sdk.service.restore_viewpoint = lambda view: None
                discarded = []
                def discard(record, *args):
                    discarded.append(record)
                    with Usd.EditContext(stage, stage.GetRootLayer()):
                        stage.RemovePrim(record.markup_path)
                adapter.discard_viewpoint = discard
                stage.SetEditTarget(stage.GetSessionLayer())
                target = stage.GetEditTarget()
                with patch.object(Sdf, 'CopySpec', return_value=False) if fail else patch.object(Sdf, 'CopySpec', wraps=Sdf.CopySpec):
                    if fail or stale:
                        with self.assertRaises(ValueError): await adapter.copy_for_edit(view)
                        self.assertEqual(len(discarded), 1)
                    else:
                        copied = await adapter.copy_for_edit(view)
                        self.assertNotEqual(copied.id, view.id)
                        self.assertEqual(copied.snapshot, b'saved PNG')
                        self.assertEqual(stage.GetPrimAtPath(draft_path + '/Arrow').GetAttribute('color').Get(), 'red')
                        self.assertEqual(product.UsdGeom.Camera(stage.GetPrimAtPath(draft_path + '/Camera')).GetFocalLengthAttr().Get(), 71)
                        with Usd.EditContext(stage, stage.GetRootLayer()):
                            stage.GetPrimAtPath(draft_path + '/Arrow').GetAttribute('color').Set('blue')
                        self.assertEqual(annotation.GetAttribute('color').Get(), 'red')
                        discard(copied)
                self.assertEqual(stage.GetEditTarget(), target)
                self.assertEqual(stage.GetRootLayer().ExportToString(), original)

    async def test_copy_edit_cancel_preserves_saved_bytes_specs_and_camera(self):
        await self.exercise()

    async def test_failed_copy_removes_only_new_draft(self):
        await self.exercise(fail=True)

    async def test_scene_generation_change_rejects_copy(self):
        await self.exercise(stale=True)
