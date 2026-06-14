"""Tests for predefined model → provider registry."""

from __future__ import annotations

import pytest

from llm_log_triage.providers import (
    MODEL_REGISTRY,
    api_key_env_for_provider,
    provider_for_model,
)


def test_registry_openai_models():
    assert provider_for_model("gpt-4o-mini") == "openai"
    assert provider_for_model("gpt-4o") == "openai"


def test_registry_anthropic_models():
    assert provider_for_model("claude-sonnet-4-6") == "anthropic"


def test_unsupported_model_raises():
    with pytest.raises(ValueError, match="Unsupported model"):
        provider_for_model("gpt-5-unknown")


def test_api_key_env_names():
    assert api_key_env_for_provider("openai") == "OPENAI_API_KEY"
    assert api_key_env_for_provider("anthropic") == "ANTHROPIC_API_KEY"


def test_supported_models_match_registry():
    from llm_log_triage.providers import SUPPORTED_MODELS

    assert set(SUPPORTED_MODELS) == set(MODEL_REGISTRY.keys())
