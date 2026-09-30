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
APP = omni.kit.app.get_app()


async def frames(count=5):
    for _ in range(count):
        await APP.next_update_async()


async def run():
    await frames(40)
    case = carb.settings.get_settings().get("/exts/issues.tag/verificationCase") or "all"
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
            for name, function in vars(module).items():
                if not name.startswith("test_") or not inspect.isfunction(function):
                    continue
                try:
                    value = function()
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
