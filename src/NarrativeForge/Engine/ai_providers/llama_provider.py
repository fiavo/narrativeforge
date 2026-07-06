from typing import AsyncIterator

from llama_cpp import Llama

from .base import AIProvider, CompletionOptions, Message, Role


class LlamaProvider(AIProvider):
    def __init__(self, model_path: str, n_ctx: int = 2048, n_gpu_layers: int = 0):
        self._llama = Llama(model_path=model_path, n_ctx=n_ctx, n_gpu_layers=n_gpu_layers)

    def _format_prompt(self, messages: list[Message]) -> str:
        parts: list[str] = []
        for msg in messages:
            token = {
                Role.SYSTEM: "<|system|>",
                Role.USER: "<|user|>",
                Role.ASSISTANT: "<|assistant|>",
            }[msg.role]
            parts.append(f"{token}\n{msg.content}")
        parts.append("<|assistant|>\n")
        return "".join(parts)

    async def complete(
        self, messages: list[Message], options: CompletionOptions | None = None
    ) -> str:
        opts = options or CompletionOptions()
        prompt = self._format_prompt(messages)
        output = self._llama(
            prompt,
            max_tokens=opts.max_tokens,
            temperature=opts.temperature,
            top_p=opts.top_p,
            stop=opts.stop or None,
            echo=False,
        )
        return output["choices"][0]["text"]

    async def stream(
        self, messages: list[Message], options: CompletionOptions | None = None
    ) -> AsyncIterator[str]:
        opts = options or CompletionOptions()
        prompt = self._format_prompt(messages)
        for chunk in self._llama(
            prompt,
            max_tokens=opts.max_tokens,
            temperature=opts.temperature,
            top_p=opts.top_p,
            stop=opts.stop or None,
            echo=False,
            stream=True,
        ):
            text = chunk["choices"][0]["text"]
            if text:
                yield text
