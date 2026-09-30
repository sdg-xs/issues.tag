"""Run behavior checks in a separate Kit process, never the user's scene."""
import asyncio
import importlib.util
import inspect
import json
import sys
import traceback
from pathlib import Path

import carb.settings
import omni.kit.app

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / 'verification' / 'python'))
APP = omni.kit.app.get_app()


async def frames(count=5):
    for _ in range(count):
        await APP.next_update_async()


async def run():
    await frames(40)
    case = carb.settings.get_settings().get("/exts/issues.tag/verificationCase") or "all"
    test_name = carb.settings.get_settings().get('/exts/issues.tag/verificationTestName') or ''
    results = []
    files = sorted((ROOT / "tests").glob("test_*.py"))
    if case != "all":
        files = [p for p in files if p.stem == "test_" + case]
    if not files:
        results.append({"name": "test_selection", "state": "FAIL", "error": f"No tests for {case}"})
    for path in files:
        try:
            spec = importlib.util.spec_from_file_location(path.stem, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for name, function in list(vars(module).items()):
                selected = name.startswith("test_") or (name.startswith("preview_") and carb.settings.get_settings().get('/exts/issues.tag/verificationVisible'))
                if not selected or not inspect.isfunction(function):
                    continue
                if test_name and name != test_name:
                    continue
                print('ISSUES_TEST_START', name, flush=True)
                try:
                    arguments = {}
                    if "service" in inspect.signature(function).parameters:
                        from test_persistence import service_for_new_scene
                        arguments["service"] = await service_for_new_scene()
                    value = function(**arguments)
                    if inspect.isawaitable(value):
                        await value
                    results.append({"name": name, "state": "PASS"})
                except Exception:
                    results.append({"name": name, "state": "FAIL", "error": traceback.format_exc()})
        except Exception:
            results.append({"name": path.stem, "state": "FAIL", "error": traceback.format_exc()})
    failed = sum(r["state"] == "FAIL" for r in results)
    report = {"passed": len(results) - failed, "failed": failed, "results": results}
    (ROOT / "verification" / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("ISSUES_VERIFICATION", json.dumps(report))
    APP.post_quit(1 if failed else 0)


if __name__ == "__main__":
    asyncio.ensure_future(run())
