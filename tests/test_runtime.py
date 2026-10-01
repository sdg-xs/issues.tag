from verify_kit import enable_extension
import importlib.util
import importlib

import omni.kit.app
import omni.usd
from verify_kit import frames


async def test_extension_activation_and_shutdown():
    assert importlib.util.find_spec("issues_tag") is not None, "Issues extension is not implemented"
    manager = omni.kit.app.get_app().get_extension_manager()
    assert enable_extension("issues.tag", True), "Issues extension cannot activate"
    from issues_tag import get_runtime_service
    assert get_runtime_service() is not None, "Issues extension is not active"
    enable_extension("issues.tag", False)
    assert get_runtime_service() is None, "Shutdown leaked the issue service"
    assert enable_extension("issues.tag", True)


async def test_markup_compatibility():
    manager = omni.kit.app.get_app().get_extension_manager()
    assert enable_extension("omni.kit.markup.core", True), "Markup Core cannot activate"
    assert enable_extension("omni.kit.tool.markup", True), "Markup Tool cannot activate"
    markup_module = importlib.import_module("omni.kit.markup.core")
    context = omni.usd.get_context()
    await context.new_stage_async()
    await frames(20)
    core = markup_module.get_instance()
    assert core is not None
    assert callable(core.create_markup) and callable(core.recall_markup), "Required supported Markup interfaces missing"


async def test_native_pin_registry_cleanup_across_reload_and_reopen(service):
    from issues_tag.elements import make_anchor
    from issues_tag import get_runtime_service
    from omni.kit.viewport.registry import RegisterScene
    from pxr import UsdGeom
    from verify_kit import ROOT
    stage = service.stage
    UsdGeom.Cube.Define(stage, '/LifecycleCube')
    issue_id = service.create_issue('Reload cleanup fixture', make_anchor(stage, '/LifecycleCube', (0, 0, 1)))
    await frames(10)
    adapter = service.viewport
    assert any(issue_id in item.visible_issue_ids for item in adapter._items)
    def factories():
        registry = importlib.import_module('omni.kit.viewport.registry').RegisterScene
        entries = registry.ordered_factories(())
        print('PIN_REGISTRY', id(registry), [(name, id(factory)) for name, factory in entries], flush=True)
        return [factory for name, factory in entries if name == 'issues.tag.Pins']
    assert len(factories()) == 1
    manager = omni.kit.app.get_app().get_extension_manager()
    assert enable_extension('issues.tag', False)
    await frames(5)
    assert not factories(), 'Disabled extension left a pin scene factory registered'
    assert not adapter._items and adapter._registration is None
    assert enable_extension('issues.tag', True)
    await frames(10)
    current = importlib.import_module('issues_tag').get_runtime_service()
    assert current.get_issue(issue_id).description == 'Reload cleanup fixture'
    assert len(factories()) == 1, 'Reactivation must restore exactly one pin overlay'
    assert callable(current.native_view_recaller)
    assert any(issue_id in item.visible_issue_ids for item in current.viewport._items)
    await current._context.new_stage_async()
    await frames(10)
    path = ROOT / 'verification' / 'lifecycle-empty.usda'
    current.stage.GetRootLayer().Export(str(path))
    await current._context.open_stage_async(str(path))
    await frames(10)
    assert not current.list_issues()
    assert all(not item.visible_issue_ids for item in current.viewport._items), 'Reopened empty scene retained pins'
    assert len(factories()) == 1
