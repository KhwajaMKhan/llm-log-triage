"""OpenTelemetry / OpenInference instrumentation for LangChain.

Instruments all LangChain calls automatically when OBS_BACKEND=otel.
Traces can be exported to Phoenix, Langfuse, etc. via OTLP endpoint.
"""

from typing import Any

_instrumented = False


def configure_otel() -> None:
    global _instrumented
    if _instrumented:
        return
    try:
        from openinference.instrumentation.langchain import LangChainInstrumentor

        LangChainInstrumentor().instrument()
        _instrumented = True
    except ImportError:
        pass


def get_otel_callbacks() -> list[Any]:
    configure_otel()
    return []
