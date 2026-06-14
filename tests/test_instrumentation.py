"""Instrumentation config tests (no live backends)."""

import os

import pytest

from llm_log_triage.instrumentation.base import configure_observability, get_callbacks


def test_default_backend_is_none(monkeypatch):
    monkeypatch.delenv("OBS_BACKEND", raising=False)
    assert configure_observability() == "none"
    assert get_callbacks() == []


def test_none_backend_disables_langsmith_tracing(monkeypatch):
    """OBS_BACKEND=none must win over LANGCHAIN_TRACING_V2=true in .env."""
    monkeypatch.setenv("OBS_BACKEND", "none")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")
    configure_observability()
    assert os.environ.get("LANGCHAIN_TRACING_V2") == "false"


def test_langsmith_backend_sets_env(monkeypatch):
    monkeypatch.setenv("OBS_BACKEND", "langsmith")
    monkeypatch.delenv("LANGCHAIN_TRACING_V2", raising=False)
    configure_observability()
    assert os.environ.get("LANGCHAIN_TRACING_V2") == "true"
    assert os.environ.get("LANGCHAIN_PROJECT") == "llm-log-triage"


def test_otel_backend_no_crash(monkeypatch):
    monkeypatch.setenv("OBS_BACKEND", "otel")
    callbacks = get_callbacks()
    assert isinstance(callbacks, list)
