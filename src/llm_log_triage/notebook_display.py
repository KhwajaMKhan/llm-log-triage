"""Display helpers for notebook eval inspection."""

from __future__ import annotations

import json

from IPython.display import Markdown, display


def show_case_header(case: dict) -> None:
    display(
        Markdown(
            f"**{case['id']}** · `{case.get('service_name', '—')}` · "
            f"adversarial={case['expected'].get('adversarial', False)}"
        )
    )


def show_log(case: dict, max_chars: int = 400) -> None:
    text = case["log_text"]
    preview = text if len(text) <= max_chars else text[:max_chars] + "…"
    display(Markdown(f"```\n{preview}\n```"))


def show_expected(case: dict) -> None:
    exp = case["expected"]
    display(Markdown(f"**Expected:** `{exp}`"))


def show_result(result, checks: dict | None = None) -> None:
    out_json = json.dumps(result.output.model_dump(mode="json"), indent=2)
    display(Markdown(f"**Triage output:**\n```json\n{out_json}\n```"))
    display(
        Markdown(
            f"_Latency: {result.latency_ms:.0f}ms · cached={result.cached} · "
            f"model={result.model} · prompt={result.prompt_version}_"
        )
    )
    if checks is not None:
        status = "✅ PASS" if checks["passed"] else "❌ FAIL"
        checks_json = json.dumps(checks, indent=2)
        display(Markdown(f"**Deterministic checks:** {status}\n```json\n{checks_json}\n```"))
