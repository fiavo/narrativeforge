from typing import AsyncIterator

import pytest

from NarrativeForge.Engine.ai_providers.base import (
    AIProvider,
    CompletionOptions,
    Message,
    Role,
)


class TestMessage:
    def test_message_creation(self):
        msg = Message(role=Role.USER, content="Hello")
        assert msg.role == Role.USER
        assert msg.content == "Hello"

    def test_system_factory(self):
        msg = Message.system("You are helpful.")
        assert msg.role == Role.SYSTEM
        assert msg.content == "You are helpful."

    def test_user_factory(self):
        msg = Message.user("What time is it?")
        assert msg.role == Role.USER

    def test_assistant_factory(self):
        msg = Message.assistant("It is noon.")
        assert msg.role == Role.ASSISTANT


class TestCompletionOptions:
    def test_defaults(self):
        opts = CompletionOptions()
        assert opts.model == ""
        assert opts.temperature == 0.7
        assert opts.max_tokens == 2048
        assert opts.top_p == 1.0
        assert opts.stop == []

    def test_custom_values(self):
        opts = CompletionOptions(model="gpt-4", temperature=0.2, max_tokens=100)
        assert opts.model == "gpt-4"
        assert opts.temperature == 0.2
        assert opts.max_tokens == 100


class FakeProvider(AIProvider):
    def __init__(self, response: str = "canned response"):
        self._response = response
        self.last_messages: list[Message] | None = None
        self.last_options: CompletionOptions | None = None

    async def complete(
        self, messages: list[Message], options: CompletionOptions | None = None
    ) -> str:
        self.last_messages = messages
        self.last_options = options
        return self._response

    async def stream(
        self, messages: list[Message], options: CompletionOptions | None = None
    ) -> AsyncIterator[str]:
        self.last_messages = messages
        self.last_options = options
        words = self._response.split()
        for word in words:
            yield word + " "


class TestFakeProvider:
    @pytest.mark.asyncio
    async def test_complete_returns_canned_response(self):
        provider = FakeProvider("hello world")
        result = await provider.complete([Message.user("hi")])
        assert result == "hello world"

    @pytest.mark.asyncio
    async def test_complete_passes_messages(self):
        provider = FakeProvider()
        msgs = [Message.system("be helpful"), Message.user("hi")]
        await provider.complete(msgs)
        assert provider.last_messages == msgs

    @pytest.mark.asyncio
    async def test_complete_passes_options(self):
        provider = FakeProvider()
        opts = CompletionOptions(temperature=0.1)
        await provider.complete([Message.user("hi")], options=opts)
        assert provider.last_options == opts

    @pytest.mark.asyncio
    async def test_stream_yields_chunks(self):
        provider = FakeProvider("a b c")
        chunks = []
        async for chunk in provider.stream([Message.user("hi")]):
            chunks.append(chunk)
        assert chunks == ["a ", "b ", "c "]

    @pytest.mark.asyncio
    async def test_stream_passes_messages(self):
        provider = FakeProvider()
        async for _ in provider.stream([Message.user("hi")]):
            pass
        assert provider.last_messages == [Message.user("hi")]
