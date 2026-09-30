import importlib.util
import importlib

import omni.kit.app
import omni.usd
from verify_kit import frames


async def test_extension_activation_and_shutdown():
    assert importlib.util.find_spec("issues_tag") is not None, "Issues extension is not implemented"
    manager = omni.kit.app.get_app().get_extension_manager()
    assert manager.set_extension_enabled_immediate("issues.tag", True), "Issues extension cannot activate"
    from issues_tag import get_runtime_service
    assert get_runtime_service() is not None, "Issues extension is not active"
    manager.set_extension_enabled_immediate("issues.tag", False)
    assert get_runtime_service() is None, "Shutdown leaked the issue service"
    assert manager.set_extension_enabled_immediate("issues.tag", True)


async def test_markup_compatibility():
    manager = omni.kit.app.get_app().get_extension_manager()
    assert manager.set_extension_enabled_immediate("omni.kit.markup.core", True), "Markup Core cannot activate"
    assert manager.set_extension_enabled_immediate("omni.kit.tool.markup", True), "Markup Tool cannot activate"
    markup_module = importlib.import_module("omni.kit.markup.core")
    context = omni.usd.get_context()
    await context.new_stage_async()
    await frames(20)
    core = markup_module.get_instance()
    assert core is not None
    assert callable(core.create_markup) and callable(core.recall_markup), "Required supported Markup interfaces missing"
