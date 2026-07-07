from .base import AIProvider, CompletionOptions, Message, Role

__all__ = [
    "AIProvider",
    "CompletionOptions",
    "Message",
    "Role",
    "LlamaProvider",
    "OpenAICompatibleProvider",
    "discover_plugin_providers",
]


def __getattr__(name: str):
    if name == "LlamaProvider":
        from .llama_provider import LlamaProvider
        return LlamaProvider
    if name == "OpenAICompatibleProvider":
        from .openai_compatible import OpenAICompatibleProvider
        return OpenAICompatibleProvider
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def discover_plugin_providers(
    plugins_dir: str | None = None,
) -> list:
    from NarrativeForge.Engine.plugins.plugin_info import PluginType
    from NarrativeForge.Engine.plugins.plugin_manager import PluginManager

    pm = PluginManager(plugins_dir=plugins_dir) if plugins_dir else PluginManager()
    all_plugins = pm.discover()
    provider_plugins = [p for p in all_plugins if p.plugin_type == PluginType.PROVIDER]
    for plugin in provider_plugins:
        pm.register(plugin)
    return provider_plugins
