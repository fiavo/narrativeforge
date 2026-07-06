from .base import AIProvider, CompletionOptions, Message, Role

__all__ = [
    "AIProvider",
    "CompletionOptions",
    "Message",
    "Role",
    "LlamaProvider",
    "OpenAICompatibleProvider",
]


def __getattr__(name: str):
    if name == "LlamaProvider":
        from .llama_provider import LlamaProvider
        return LlamaProvider
    if name == "OpenAICompatibleProvider":
        from .openai_compatible import OpenAICompatibleProvider
        return OpenAICompatibleProvider
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
