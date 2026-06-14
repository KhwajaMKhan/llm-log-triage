"""File-based response cache for golden-set reruns.

Avoids re-spending API credits when pytest re-runs the same log+model+prompt combo.
Key = SHA256(log, service, model, prompt_version) → JSON file under .cache/llm-log-triage/.
"""

import hashlib
import json
import os
from pathlib import Path

from llm_log_triage.schema import TriageOutput


def _cache_dir() -> Path:
    base = os.getenv("LOG_TRIAGE_CACHE_DIR", ".cache/llm-log-triage")
    path = Path(base)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _key(log_text: str, service_name: str | None, model: str, prompt_version: str) -> str:
    payload = json.dumps(
        {"log": log_text, "service": service_name, "model": model, "prompt": prompt_version},
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def get_cached(
    log_text: str,
    service_name: str | None,
    model: str,
    prompt_version: str,
) -> TriageOutput | None:
    path = _cache_dir() / f"{_key(log_text, service_name, model, prompt_version)}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return TriageOutput.model_validate(data)


def set_cached(
    log_text: str,
    service_name: str | None,
    model: str,
    prompt_version: str,
    output: TriageOutput,
) -> None:
    path = _cache_dir() / f"{_key(log_text, service_name, model, prompt_version)}.json"
    path.write_text(output.model_dump_json(indent=2))
