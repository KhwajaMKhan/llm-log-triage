"""LLM-as-Judge for LLM log triage triage output — coherence + actionability scoring.

This is a SEPARATE LLM call from chain.py (the triage model).
Flow: chain.invoke() produces TriageOutput → judge_triage() scores it 1-5.

Charter pass bar: coherence >= 4 AND actionability >= 4 (see passes_judge).
Used by tests/test_judge.py and future LangSmith/Braintrust eval integrations.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from llm_log_triage.instrumentation.base import get_callbacks
from llm_log_triage.providers import resolve_provider
from llm_log_triage.schema import TriageOutput

load_dotenv()

# Reviewer model — defaults to same as triage model unless LOG_TRIAGE_JUDGE_MODEL is set
JUDGE_MODEL = os.getenv("LOG_TRIAGE_JUDGE_MODEL", os.getenv("LOG_TRIAGE_DEFAULT_MODEL", "gpt-4o-mini"))
PASS_THRESHOLD = int(os.getenv("LOG_TRIAGE_JUDGE_PASS_SCORE", "4"))


class JudgeScore(BaseModel):
    """Structured scores returned by the judge LLM."""

    coherence: int = Field(..., ge=1, le=5, description="Is the triage logically consistent with the log?")
    actionability: int = Field(..., ge=1, le=5, description="Is suggested_action concrete for on-call?")
    rationale: str = Field(..., min_length=1)


# Prompt for the reviewer — different role than the triage system prompt in prompts.py
JUDGE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an SRE QA reviewer scoring log triage output.\n"
            "Score 1-5 on:\n"
            "- coherence: assessment matches log evidence, no contradictions\n"
            "- actionability: suggested_action is specific and executable\n"
            "Pass bar for each dimension: >= 4.",
        ),
        (
            "human",
            "Log:\n{log_text}\n\n"
            "Triage JSON:\n"
            "severity: {severity}\n"
            "category: {category}\n"
            "likely_cause: {likely_cause}\n"
            "suggested_action: {suggested_action}\n"
            "confidence: {confidence}\n"
            "evidence_lines: {evidence_lines}",
        ),
    ]
)


def _build_judge_llm(model: str):
    """Same provider routing as chain.py (providers.resolve_provider)."""
    if resolve_provider(model) == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=model)
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=model, temperature=0)


def _judge_run_config(
    model: str,
    interface: str,
    case_id: str | None,
) -> RunnableConfig:
    """LangSmith: tags are filterable in UI; metadata alone is easy to miss on child spans."""
    tags = ["llm-log-triage", "role:judge", f"interface:{interface}", f"model:{model}"]
    metadata: dict[str, str] = {
        "app": "llm-log-triage",
        "role": "judge",
        "interface": interface,
        "model": model,
    }
    run_name = "judge"
    if case_id:
        tags.append(f"case_id:{case_id}")
        metadata["case_id"] = case_id
        run_name = f"judge-{case_id}"
    return RunnableConfig(
        callbacks=get_callbacks(),
        metadata=metadata,
        tags=tags,
        run_name=run_name,
    )


def judge_triage(
    log_text: str,
    output: TriageOutput,
    *,
    model: str = JUDGE_MODEL,
    interface: str = "unknown",
    case_id: str | None = None,
) -> JudgeScore:
    """Score one triage result with a second LLM call (the 'judge')."""
    chain = JUDGE_PROMPT | _build_judge_llm(model).with_structured_output(JudgeScore)
    config = _judge_run_config(model, interface, case_id)
    return chain.invoke(
        {
            "log_text": log_text,
            "severity": output.severity.value,
            "category": output.category.value,
            "likely_cause": output.likely_cause,
            "suggested_action": output.suggested_action,
            "confidence": output.confidence,
            "evidence_lines": output.evidence_lines,
        },
        config=config,
    )


def passes_judge(score: JudgeScore, threshold: int = PASS_THRESHOLD) -> bool:
    """Both dimensions must meet threshold — one weak score fails the case."""
    return score.coherence >= threshold and score.actionability >= threshold
