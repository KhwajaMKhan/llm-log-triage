#!/usr/bin/env python3
"""Compare llm-log-triage (A) vs direct chat LLM (B) vs Jev (C) on golden-set cases."""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import tiktoken
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from llm_log_triage.chain import invoke  # noqa: E402
from llm_log_triage.prompts import (  # noqa: E402
    ADVERSARIAL_RULES,
    CATEGORY_RUBRIC,
    FEW_SHOT,
    LOG_LEVEL_RULES,
    SEVERITY_RUBRIC,
    get_prompt,
)
from llm_log_triage.schema import Category, Severity  # noqa: E402

DEFAULT_CASE_IDS = ["gs-001", "gs-002", "adv-002"]
RUNS = 3
MODEL = "gpt-4o-mini"
PROMPT_VERSION = "v3"

OPENAI_INPUT_PER_TOKEN = 0.15 / 1_000_000
OPENAI_OUTPUT_PER_TOKEN = 0.60 / 1_000_000
JEV_INPUT_PER_TOKEN = 42 / 1_000_000_000  # $42/Btok — $0.042/MTok input

REASONING_SYSTEM = (
    "You are an expert SRE triaging production logs.\n\n"
    "Think step by step in detail before deciding severity and category. "
    "Write at least 8 sentences of reasoning in a \"reasoning\" field, then fill the triage JSON.\n\n"
    + SEVERITY_RUBRIC
    + "\n"
    + CATEGORY_RUBRIC
    + "\n"
    + LOG_LEVEL_RULES
    + "\n"
    + ADVERSARIAL_RULES
    + "\n"
    + FEW_SHOT
    + "\n\nReturn ONLY valid JSON with keys:\n"
    "reasoning, severity, category, likely_cause, suggested_action, confidence, evidence_lines (array of strings).\n\n"
    "severity must be one of: SEV1, SEV2, SEV3, SEV4, unknown\n"
    "category must be one of: connectivity, resource, auth, config, dependency, unknown\n"
    "confidence is 0.0–1.0"
)


class ReasoningOutput(BaseModel):
    reasoning: str = Field(..., min_length=50)
    severity: Severity
    category: Category
    likely_cause: str
    suggested_action: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_lines: list[str] = Field(default_factory=list)


JEV_QUESTIONS = {
    "category": {
        "type": "choice",
        "instructions": "Primary incident category for this log line",
        "criteria": {
            "connectivity": "Network/DB connection refused, DNS, deadlock, timeouts to peers",
            "resource": "OOM, memory/disk pressure, eviction, rate limits, capacity",
            "auth": "JWT, SAML, SMTP, credential or authentication failures",
            "config": "YAML parse errors, cert expired, vault sealed, misconfiguration",
            "dependency": "Upstream latency, external API 503, third-party outage",
            "unknown": "Insufficient context, generic 500, or unparseable input",
        },
    },
    "severity": {
        "type": "choice",
        "instructions": "Incident severity for paging/on-call",
        "criteria": {
            "SEV1": "Total outage, OOMKilled, pod evicted, vault sealed, data loss risk",
            "SEV2": "DB unreachable, connection refused, cert expired, major subsystem down",
            "SEV3": "Single-user auth fail, WARN latency, disk warning, subset impact",
            "SEV4": "INFO routine operations, successful jobs",
            "unknown": "Empty, truncated, keyboard mash, or spam — not pageable",
        },
    },
}


def typesafe_api_key() -> str:
    return os.getenv("TYPESAFE_API_KEY", "") or os.getenv("TYPESCRIPT_AI_API_KEY", "")


@dataclass
class RunRecord:
    lane: str
    case_id: str
    run: int
    latency_ms: float
    input_tokens: int
    output_tokens: int
    cost_usd: float
    severity: str | None
    category: str | None
    confidence: float | None
    category_ok: bool
    severity_ok: bool
    adversarial_ok: bool | None
    error: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


def load_cases(case_ids: list[str]) -> list[dict[str, Any]]:
    golden = json.loads((REPO_ROOT / "data" / "golden_set.json").read_text())
    by_id = {c["id"]: c for c in golden["cases"]}
    missing = [i for i in case_ids if i not in by_id]
    if missing:
        raise SystemExit(f"Missing cases in golden_set: {missing}")
    return [by_id[i] for i in case_ids]


def score(
    case: dict[str, Any], severity: str | None, category: str | None, confidence: float | None
) -> tuple[bool, bool, bool | None]:
    exp = case["expected"]
    cat_ok = category == exp["category"]
    sev_ok = severity == exp["severity"]
    adv_ok: bool | None = None
    if exp.get("adversarial") and "max_confidence" in exp and confidence is not None:
        adv_ok = confidence <= exp["max_confidence"]
    return cat_ok, sev_ok, adv_ok


def openai_cost(inp: int, out: int) -> float:
    return inp * OPENAI_INPUT_PER_TOKEN + out * OPENAI_OUTPUT_PER_TOKEN


def jev_cost(inp: int) -> float:
    return inp * JEV_INPUT_PER_TOKEN


def _token_usage(meta: dict[str, Any] | None) -> tuple[int, int]:
    if not meta:
        return 0, 0
    usage = meta.get("token_usage") or meta.get("usage") or {}
    return int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0))


def _estimate_tokens(text: str, model: str = MODEL) -> int:
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))


def lane_a(case: dict[str, Any], run: int) -> RunRecord:
    os.environ["OBS_BACKEND"] = "none"
    t0 = time.perf_counter()
    err: str | None = None
    inp_t = out_t = 0
    severity = category = None
    confidence = None
    try:
        result = invoke(
            case["log_text"],
            case.get("service_name"),
            model=MODEL,
            prompt_version=PROMPT_VERSION,
            use_cache=False,
            interface="jev-benchmark-a",
            case_id=case["id"],
        )
        out = result.output
        severity, category, confidence = out.severity.value, out.category.value, out.confidence
        prompt = get_prompt(PROMPT_VERSION)
        service = case.get("service_name") or "unknown"
        prompt_text = prompt.format(log_text=case["log_text"], service_name=service)
        inp_t = _estimate_tokens(str(prompt_text))
        out_t = _estimate_tokens(out.model_dump_json())
        latency = (time.perf_counter() - t0) * 1000
    except Exception as e:
        latency = (time.perf_counter() - t0) * 1000
        err = str(e)
    cat_ok, sev_ok, adv_ok = score(case, severity, category, confidence)
    return RunRecord(
        lane="A",
        case_id=case["id"],
        run=run,
        latency_ms=round(latency, 1),
        input_tokens=inp_t,
        output_tokens=out_t,
        cost_usd=round(openai_cost(inp_t, out_t), 8),
        severity=severity,
        category=category,
        confidence=confidence,
        category_ok=cat_ok,
        severity_ok=sev_ok,
        adversarial_ok=adv_ok,
        error=err,
    )


def _parse_reasoning_json(text: str) -> ReasoningOutput:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return ReasoningOutput.model_validate(json.loads(text))


def lane_b(case: dict[str, Any], run: int) -> RunRecord:
    llm = ChatOpenAI(model=MODEL, temperature=0)
    user = f"Service: {case.get('service_name') or 'unknown'}\nLog:\n{case['log_text']}"
    t0 = time.perf_counter()
    err: str | None = None
    inp_t = out_t = 0
    severity = category = None
    confidence = None
    reasoning_len = 0
    try:
        msg = llm.invoke([SystemMessage(content=REASONING_SYSTEM), HumanMessage(content=user)])
        inp_t, out_t = _token_usage(getattr(msg, "response_metadata", None))
        parsed = _parse_reasoning_json(str(msg.content))
        severity = parsed.severity.value
        category = parsed.category.value
        confidence = parsed.confidence
        reasoning_len = len(parsed.reasoning)
        latency = (time.perf_counter() - t0) * 1000
    except Exception as e:
        latency = (time.perf_counter() - t0) * 1000
        err = str(e)
    cat_ok, sev_ok, adv_ok = score(case, severity, category, confidence)
    return RunRecord(
        lane="B",
        case_id=case["id"],
        run=run,
        latency_ms=round(latency, 1),
        input_tokens=inp_t,
        output_tokens=out_t,
        cost_usd=round(openai_cost(inp_t, out_t), 8),
        severity=severity,
        category=category,
        confidence=confidence,
        category_ok=cat_ok,
        severity_ok=sev_ok,
        adversarial_ok=adv_ok,
        error=err,
        extra={"reasoning_chars": reasoning_len},
    )


def lane_c(case: dict[str, Any], run: int, api_key: str) -> RunRecord:
    state = case["log_text"]
    if case.get("service_name"):
        state = f"service={case['service_name']}\n{state}"
    payload = {"state": state, "model": "jev-latest", "questions": JEV_QUESTIONS}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    t0 = time.perf_counter()
    err: str | None = None
    severity = category = None
    confidence = None
    inp_t = out_t = 0
    extra: dict[str, Any] = {}
    try:
        resp = httpx.post(
            "https://api.typesafe.ai/v1/systemone",
            headers=headers,
            json=payload,
            timeout=30.0,
        )
        latency = (time.perf_counter() - t0) * 1000
        if resp.status_code != 200:
            err = f"HTTP {resp.status_code}: {resp.text[:300]}"
        else:
            body = resp.json()
            usage = body.get("usage", {})
            inp_t = int(usage.get("input_tokens", 0))
            out_t = int(usage.get("output_tokens", 0))
            answers = body.get("answers", {})
            cat_a = answers.get("category", {})
            sev_a = answers.get("severity", {})
            category = cat_a.get("choice")
            severity = sev_a.get("choice")
            confs = [x.get("confidence") for x in (cat_a, sev_a) if x.get("confidence") is not None]
            confidence = statistics.mean(confs) if confs else None
            extra = {
                "model": body.get("model"),
                "category_probs": cat_a.get("probabilities"),
                "severity_probs": sev_a.get("probabilities"),
                "category_confidence": cat_a.get("confidence"),
                "severity_confidence": sev_a.get("confidence"),
            }
    except Exception as e:
        latency = (time.perf_counter() - t0) * 1000
        err = str(e)
    cat_ok, sev_ok, adv_ok = score(case, severity, category, confidence)
    return RunRecord(
        lane="C",
        case_id=case["id"],
        run=run,
        latency_ms=round(latency, 1),
        input_tokens=inp_t,
        output_tokens=out_t,
        cost_usd=round(jev_cost(inp_t), 8),
        severity=severity,
        category=category,
        confidence=round(confidence, 4) if confidence is not None else None,
        category_ok=cat_ok,
        severity_ok=sev_ok,
        adversarial_ok=adv_ok,
        error=err,
        extra=extra,
    )


def median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def write_summary(records: list[RunRecord], case_ids: list[str], ts: str, path: Path) -> None:
    lines = [
        f"# Jev benchmark summary — {ts}",
        "",
        f"Cases: {', '.join(case_ids)} · medians below.",
        "",
        "## Setup",
        "",
        f"- Model (A/B): `{MODEL}`, prompt `{PROMPT_VERSION}`",
        "- Lane A: `llm-log-triage` structured output (CLI path)",
        "- Lane B: Direct chat LLM — think out loud first (same model, no app)",
        "- Lane C: Jev `jev-latest` — Choice questions for category + severity",
        "- Jev pricing: $42/Btok ($0.042/MTok input); output tokens free",
        "",
        "## Median latency (ms)",
        "",
        "| Case | A | B | C |",
        "|------|---|---|---|",
    ]
    for cid in case_ids:
        row = [cid]
        for lane in "ABC":
            lat = [r.latency_ms for r in records if r.case_id == cid and r.lane == lane and not r.error]
            row.append(f"{median(lat):.0f}" if lat else "—")
        lines.append("| " + " | ".join(row) + " |")

    lines += ["", "## Median cost per invoke (USD)", "", "| Case | A | B | C |", "|------|---|---|---|"]
    for cid in case_ids:
        row = [cid]
        for lane in "ABC":
            costs = [r.cost_usd for r in records if r.case_id == cid and r.lane == lane and not r.error]
            row.append(f"${median(costs):.6f}" if costs else "—")
        lines.append("| " + " | ".join(row) + " |")

    path.write_text("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Jev vs llm-log-triage benchmark")
    parser.add_argument("--lanes", default="ABC", help="Lanes to run: A, B, C, or ABC")
    parser.add_argument("--cases", default=",".join(DEFAULT_CASE_IDS), help="Comma-separated case ids")
    parser.add_argument("--runs", type=int, default=RUNS, help="Runs per case per lane")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "docs/jev-benchmark-runs",
        help="Where to write JSON + SUMMARY.md",
    )
    args = parser.parse_args(argv)

    load_dotenv(REPO_ROOT / ".env")
    case_ids = [c.strip() for c in args.cases.split(",") if c.strip()]
    wanted = set(args.lanes.upper())
    out_dir: Path = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    typesafe_key = typesafe_api_key()
    if "C" in wanted and not typesafe_key:
        print("WARNING: lane C requested but TYPESAFE_API_KEY not set — skipping C")
        wanted.discard("C")

    cases = load_cases(case_ids)
    records: list[RunRecord] = []
    print(f"Running: {len(cases)} cases × {args.runs} runs × lanes {''.join(sorted(wanted))}")
    for case in cases:
        for run in range(1, args.runs + 1):
            print(f"  {case['id']} run {run} …", flush=True)
            if "A" in wanted:
                records.append(lane_a(case, run))
            if "B" in wanted:
                records.append(lane_b(case, run))
            if "C" in wanted:
                records.append(lane_c(case, run, typesafe_key))

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    out_json = out_dir / f"lab_{ts}.json"
    out_json.write_text(json.dumps([asdict(r) for r in records], indent=2))
    summary_path = out_dir / "SUMMARY.md"
    write_summary(records, case_ids, ts, summary_path)
    print(f"\nWrote {out_json}")
    print(f"Wrote {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
