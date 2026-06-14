"""Tests for provider routing (MODEL_REGISTRY, heuristics, LOG_TRIAGE_PROVIDER)."""

from __future__ import annotations

import os

import pytest

from llm_log_triage.providers import (
    MODEL_REGISTRY,
    api_key_env_for_provider,
    provider_for_model,
    resolve_provider,
)


def test_registry_models():
    assert MODEL_REGISTRY["gpt-4o-mini"] == "openai"
    assert MODEL_REGISTRY["claude-sonnet-4-6"] == "anthropic"


def test_provider_override():
    assert provider_for_model("future-model-xyz", provider_override="anthropic") == "anthropic"


def test_heuristic_claude_prefix():
    assert provider_for_model("claude-future-99") == "anthropic"


def test_heuristic_gpt_prefix():
    assert provider_for_model("gpt-5-nano") == "openai"


def test_unknown_model_raises():
    with pytest.raises(ValueError, match="LOG_TRIAGE_PROVIDER"):
        provider_for_model("totally-unknown-vendor-model")


def test_resolve_provider_from_env(monkeypatch):
    monkeypatch.setenv("LOG_TRIAGE_PROVIDER", "openai")
    assert resolve_provider("future-model-xyz") == "openai"


def test_api_key_env_names():
    assert api_key_env_for_provider("openai") == "OPENAI_API_KEY"
    assert api_key_env_for_provider("anthropic") == "ANTHROPIC_API_KEY"
