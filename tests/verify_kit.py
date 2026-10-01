"""Run behavior checks in a separate Kit process, never the user's scene."""
import asyncio
import importlib.util
import inspect
import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

import carb.settings
import omni.kit.app

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / 'verification' / 'python'))
sys.path.insert(0, str(ROOT / 'tools'))
from verification_progress import replace_progress
APP = omni.kit.app.get_app()


def qualify_runtime():
    dependency_root = carb.settings.get_settings().get('/exts/issues.tag/verificationDependencyRoot')
    if not dependency_root:
        raise ValueError('Dependency root is not configured.')
    sys.path.insert(0, str(ROOT / 'tools'))
    from verification_dependencies import qualify_extension_paths
    manager = APP.get_extension_manager()
    paths = [(entry['id'], manager.get_extension_path(entry['id']))
             for entry in manager.get_extensions() if entry['enabled']]
    qualified = qualify_extension_paths(paths, dependency_root, ROOT)
    (ROOT / 'verification' / 'loaded-extensions.json').write_text(json.dumps(qualified, indent=2), encoding='utf-8')
    return qualified


def enable_extension(name, enabled=True):
    result = APP.get_extension_manager().set_extension_enabled_immediate(name, enabled)
    qualify_runtime()
    return result


async def frames(count=5):
    for _ in range(count):
        await APP.next_update_async()


def write_progress(results, phase, test=None):
    report = {
        'updated_at': datetime.now(timezone.utc).isoformat(),
        'phase': phase,
        'current_test': test,
        'passed': sum(result['state'] == 'PASS' for result in results),
        'failed': sum(result['state'] == 'FAIL' for result in results),
        'results': results,
    }
    destination = ROOT / 'verification' / 'progress.json'
    temporary = destination.with_suffix('.json.tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    replace_progress(temporary, destination)
    print('ISSUES_TEST_PHASE', test or 'run', phase, flush=True)


async def run():
    results = []
    write_progress(results, 'startup')
    await frames(40)
    dependency_root = carb.settings.get_settings().get('/exts/issues.tag/verificationDependencyRoot')
    if not dependency_root:
        print('ISSUES_ISOLATION_FAIL dependency root is not configured', flush=True)
        results.append({'name': 'isolation', 'state': 'FAIL', 'error': 'Dependency root is not configured.'})
        write_progress(results, 'isolation_failed')
        APP.post_quit(1)
        return
    try:
        qualified = qualify_runtime()
        print('ISSUES_ISOLATION_PASS', len(qualified), 'enabled extensions', flush=True)
    except Exception:
        error = traceback.format_exc()
        print('ISSUES_ISOLATION_FAIL', error, flush=True)
        results.append({'name': 'isolation', 'state': 'FAIL', 'error': error})
        write_progress(results, 'isolation_failed')
        APP.post_quit(1)
        return
    case = carb.settings.get_settings().get("/exts/issues.tag/verificationCase") or "all"
    test_name = carb.settings.get_settings().get('/exts/issues.tag/verificationTestName') or ''
    files = sorted((ROOT / "tests").glob("test_*.py"))
    if case != "all":
        files = [p for p in files if p.stem == "test_" + case]
    else:
        files = [p for p in files if p.stem != 'test_capture_probe']
    if not files:
        results.append({"name": "test_selection", "state": "FAIL", "error": f"No tests for {case}"})
    for path in files:
        try:
            write_progress(results, 'module_import', path.stem)
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
                phase = 'fixture'
                try:
                    write_progress(results, phase, name)
                    arguments = {}
                    if "service" in inspect.signature(function).parameters:
                        from test_persistence import service_for_new_scene
                        arguments["service"] = await service_for_new_scene()
                    phase = 'dependencies'
                    write_progress(results, phase, name)
                    if path.stem == 'test_native_recall':
                        enable_extension('omni.kit.tool.markup', False)
                        if not enable_extension('omni.kit.markup.core'):
                            raise ValueError('Cannot enable private Markup Core')
                    if path.stem in ('test_markup', 'test_workflow'):
                        for dependency in ('omni.kit.markup.core', 'omni.kit.tool.markup'):
                            if not enable_extension(dependency):
                                raise ValueError(f'Cannot enable required private dependency: {dependency}')
                    qualify_runtime()
                    phase = 'body'
                    write_progress(results, phase, name)
                    value = function(**arguments)
                    if inspect.isawaitable(value):
                        await value
                    phase = 'post_test_qualification'
                    write_progress(results, phase, name)
                    qualify_runtime()
                    results.append({"name": name, "state": "PASS"})
                except Exception:
                    results.append({"name": name, "state": "FAIL", "phase": phase, "error": traceback.format_exc()})
                write_progress(results, 'outcome', name)
                print('ISSUES_TEST_RESULT', json.dumps(results[-1]), flush=True)
        except Exception:
            results.append({"name": path.stem, "state": "FAIL", "error": traceback.format_exc()})
            write_progress(results, 'outcome', path.stem)
            print('ISSUES_TEST_RESULT', json.dumps(results[-1]), flush=True)
    failed = sum(r["state"] == "FAIL" for r in results)
    if not results:
        results.append({'name': 'test_selection', 'state': 'FAIL', 'error': 'No matching checks were executed.'})
        failed = 1
    report = {"passed": len(results) - failed, "failed": failed, "results": results}
    (ROOT / "verification" / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_progress(results, 'complete')
    print("ISSUES_VERIFICATION", json.dumps(report))
    APP.post_quit(1 if failed else 0)


if __name__ == "__main__":
    asyncio.ensure_future(run())
