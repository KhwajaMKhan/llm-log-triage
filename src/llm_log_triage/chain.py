"""LLM log triage LCEL chain: prompt -> LLM -> structured JSON triage output.

Architecture (single entry point):
  cli.py / ui/streamlit_app.py / notebook / tests
                    │
                    ▼
              invoke()  ← you are here
                    │
    ┌───────────────┼───────────────┐
    ▼               ▼               ▼
  cache.py      prompts.py     instrumentation/
  (optional)    + schema.py      (OTel/LangSmith)
                    │
                    ▼
            LangChain LCEL: prompt | llm.with_structured_output(TriageOutput)
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig

from llm_log_triage.cache import get_cached, set_cached
from llm_log_triage.instrumentation.base import get_callbacks
from llm_log_triage.prompts import get_prompt
from llm_log_triage.schema import TriageInput, TriageOutput

load_dotenv()

DEFAULT_MODEL = os.getenv("LOG_TRIAGE_DEFAULT_MODEL", "gpt-4o-mini")
DEFAULT_PROMPT = os.getenv("LOG_TRIAGE_DEFAULT_PROMPT_VERSION", "v3")

# Verified via live invoke (prompt v3); Streamlit selectbox uses this list.
SUPPORTED_MODELS: tuple[str, ...] = (
    "gpt-4o-mini",
    "gpt-4o",
    "claude-sonnet-4-6",
    "claude-opus-4-7",
)


@dataclass
class InvokeResult:
    output: TriageOutput
    latency_ms: float
    model: str
    prompt_version: str
    cached: bool


def _build_llm(model: str):
    """Pick OpenAI or Anthropic client based on model name prefix."""
    if model.startswith("claude") or model.startswith("anthropic"):
        from langchain_anthropic import ChatAnthropic

        # Claude 4+ (e.g. opus-4-7) rejects `temperature`; omit for all Anthropic models.
        return ChatAnthropic(model=model)
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=model, temperature=0)


def build_chain(model: str = DEFAULT_MODEL, prompt_version: str = DEFAULT_PROMPT):
    """Assemble the LangChain runnable: ChatPromptTemplate piped into structured-output LLM."""
    prompt = get_prompt(prompt_version)
    llm = _build_llm(model).with_structured_output(TriageOutput)
    return prompt | llm


def invoke(
    log_text: str,
    service_name: str | None = None,
    *,
    model: str = DEFAULT_MODEL,
    prompt_version: str = DEFAULT_PROMPT,
    use_cache: bool = True,
    interface: str = "unknown",
    case_id: str | None = None,
) -> InvokeResult:
    """Run log triage. Single entry point for CLI, Streamlit, notebook, and pytest."""
    inp = TriageInput(log_text=log_text, service_name=service_name)

    # 1) Return cached result if we've seen this exact input before
    if use_cache:
        cached = get_cached(inp.log_text, inp.service_name, model, prompt_version)
        if cached is not None:
            return InvokeResult(
                output=cached,
                latency_ms=0.0,
                model=model,
                prompt_version=prompt_version,
                cached=True,
            )

    # 2) Build chain and attach observability callbacks (LangSmith/OTel via env)
    chain = build_chain(model=model, prompt_version=prompt_version)
    service = inp.service_name or "unknown"
    tags = [f"llm-log-triage", f"interface:{interface}", f"prompt:{prompt_version}", f"model:{model}"]
    metadata: dict[str, str] = {
        "app": "llm-log-triage",
        "interface": interface,
        "prompt_version": prompt_version,
        "model": model,
        "service_name": service,
    }
    run_name = "triage"
    if case_id:
        tags.append(f"case_id:{case_id}")
        metadata["case_id"] = case_id
        run_name = f"triage-{case_id}"
    config = RunnableConfig(
        callbacks=get_callbacks(),
        metadata=metadata,
        tags=tags,
        run_name=run_name,
    )

    # 3) Run LLM and measure latency for scorecard / debugging
    start = time.perf_counter()
    output: TriageOutput = chain.invoke(
        {"log_text": inp.log_text, "service_name": service},
        config=config,
    )
    latency_ms = (time.perf_counter() - start) * 1000

    if use_cache:
        set_cached(inp.log_text, inp.service_name, model, prompt_version, output)

    return InvokeResult(
        output=output,
        latency_ms=latency_ms,
        model=model,
        prompt_version=prompt_version,
        cached=False,
    )
