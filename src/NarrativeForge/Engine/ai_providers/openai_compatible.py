from typing import AsyncIterator

import httpx

from .base import AIProvider, CompletionOptions, Message


class OpenAICompatibleProvider(AIProvider):
    def __init__(self, base_url: str, api_key: str = "no-key", model: str = ""):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._default_model = model
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=60.0,
        )

    def _build_payload(
        self, messages: list[Message], options: CompletionOptions, stream: bool = False
    ) -> dict:
        model = options.model or self._default_model
        return {
            "model": model,
            "messages": [{"role": m.role.value, "content": m.content} for m in messages],
            "temperature": options.temperature,
            "max_tokens": options.max_tokens,
            "top_p": options.top_p,
            "stream": stream,
        }

    async def complete(
        self, messages: list[Message], options: CompletionOptions | None = None
    ) -> str:
        opts = options or CompletionOptions()
        payload = self._build_payload(messages, opts, stream=False)
        resp = await self._client.post("/v1/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    async def stream(
        self, messages: list[Message], options: CompletionOptions | None = None
    ) -> AsyncIterator[str]:
        opts = options or CompletionOptions()
        payload = self._build_payload(messages, opts, stream=True)
        async with self._client.stream("POST", "/v1/chat/completions", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[len("data: "):]
                if data_str.strip() == "[DONE]":
                    break
                import json
                data = json.loads(data_str)
                delta = data["choices"][0].get("delta", {})
                text = delta.get("content")
                if text:
                    yield text
