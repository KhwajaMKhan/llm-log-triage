"""LangSmith setup helpers.

LangSmith reads LANGCHAIN_* env vars — no explicit callback object needed.
configure_langsmith() turns tracing on before chain.invoke() runs.
"""

import os


def configure_langsmith(project: str | None = None) -> None:
    """Enable LangSmith tracing via environment variables."""
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ.setdefault("LANGCHAIN_PROJECT", project or "llm-log-triage")
    if project:
        os.environ["LANGCHAIN_PROJECT"] = project
