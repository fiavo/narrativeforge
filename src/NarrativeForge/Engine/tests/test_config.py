"""Tests for configuration module."""
import pytest
from NarrativeForge.Engine.config import Config


@pytest.mark.unit
class TestConfig:
    """Test configuration loading and validation."""

    def test_default_config(self):
        """Test that default config loads correctly."""
        config = Config()
        assert config.host == "127.0.0.1"
        assert config.port == 8000
        assert config.default_model == "llama-3-8b"
        assert config.max_context_tokens == 4096
        assert config.temperature == 0.7

    def test_custom_config(self):
        """Test that custom config overrides defaults."""
        config = Config(
            host="0.0.0.0",
            port=9000,
            default_model="custom-model",
            temperature=0.5,
        )
        assert config.host == "0.0.0.0"
        assert config.port == 9000
        assert config.default_model == "custom-model"
        assert config.temperature == 0.5

    def test_temperature_validation(self):
        """Test temperature is a float."""
        config = Config(temperature=0.8)
        assert isinstance(config.temperature, float)
        assert 0 <= config.temperature <= 2
