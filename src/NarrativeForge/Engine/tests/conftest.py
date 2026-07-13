"""Shared test fixtures and configuration."""
import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from NarrativeForge.Engine.config import Config
from NarrativeForge.Engine.storage.database import Database
from NarrativeForge.Engine.ai_providers.base import AIProvider, Message, CompletionOptions


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_config():
    """Provide test configuration."""
    return Config(
        host="127.0.0.1",
        port=8001,
        database_url="sqlite+aiosqlite:///:memory:",
        default_model="test-model",
        max_context_tokens=4096,
        temperature=0.7,
    )


@pytest.fixture
async def test_db(test_config):
    """Provide an in-memory test database."""
    db = Database(test_config.database_url)
    await db.init()
    yield db
    await db.close()


@pytest.fixture
def mock_ai_provider():
    """Provide a mock AI provider."""
    provider = AsyncMock(spec=AIProvider)
    provider.complete = AsyncMock(return_value="Mock AI response")
    provider.stream = AsyncMock()
    return provider


@pytest.fixture
def sample_messages():
    """Provide sample messages for testing."""
    return [
        Message.system("You are a helpful narrative assistant."),
        Message.user("Generate a fantasy story."),
    ]


@pytest.fixture
def completion_options():
    """Provide sample completion options."""
    return CompletionOptions(
        model="test-model",
        temperature=0.7,
        max_tokens=2048,
        top_p=0.9,
    )
