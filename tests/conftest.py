"""Shared pytest fixtures."""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = ROOT / "data" / "golden_set.json"


@pytest.fixture(scope="session")
def golden_cases() -> list[dict]:
    data = json.loads(GOLDEN_PATH.read_text())
    return data["cases"]


@pytest.fixture(scope="session")
def normal_cases(golden_cases) -> list[dict]:
    return [c for c in golden_cases if not c["expected"].get("adversarial")]


@pytest.fixture(scope="session")
def adversarial_cases(golden_cases) -> list[dict]:
    return [c for c in golden_cases if c["expected"].get("adversarial")]
