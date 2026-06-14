"""Observability backend selection.

Set OBS_BACKEND in .env (none | langsmith | otel); chain.py stays frozen.
"""

import os
from typing import Any


def configure_observability() -> str:
    """Configure env/callbacks for the selected backend. Returns backend name."""
    backend = os.getenv("OBS_BACKEND", "none").lower()

    if backend == "langsmith":
        from llm_log_triage.instrumentation.langsmith import configure_langsmith

        configure_langsmith()
    elif backend == "otel":
        from llm_log_triage.instrumentation.otel import configure_otel

        configure_otel()
    else:
        # OBS_BACKEND=none — suppress LangChain auto-tracing (avoids 401 if key missing)
        os.environ["LANGCHAIN_TRACING_V2"] = "false"

    return backend


def get_callbacks() -> list[Any]:
    """Return LangChain callbacks for the configured observability backend."""
    backend = configure_observability()
    callbacks: list[Any] = []

    if backend == "otel":
        from llm_log_triage.instrumentation.otel import get_otel_callbacks

        callbacks.extend(get_otel_callbacks())

    return callbacks
