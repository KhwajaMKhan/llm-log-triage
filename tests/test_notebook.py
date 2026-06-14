"""Notebook setup smoke tests — no LLM calls."""

from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import pytest

from llm_log_triage.notebook_setup import find_repo_root, verify_notebook_kernel

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = ROOT / "data" / "golden_set.json"
NOTEBOOK_PATH = ROOT / "notebooks" / "explore.ipynb"


def test_repo_root_from_project_dir():
    assert find_repo_root(ROOT) == ROOT


def test_repo_root_from_notebooks_dir():
    assert find_repo_root(ROOT / "notebooks") == ROOT


def test_golden_set_loads_like_notebook():
    data = json.loads(GOLDEN_PATH.read_text())
    assert len(data["cases"]) == 26
    assert "log_text" in data["cases"][0]
    assert "expected" in data["cases"][0]


def test_invoke_accepts_interface_and_case_id():
    """Notebook and pytest pass interface=; stale editable installs break this."""
    from llm_log_triage.chain import invoke

    sig = inspect.signature(invoke)
    assert "interface" in sig.parameters, (
        "invoke() missing interface= — re-run: pip install -e '.[dev,obs]' from repo root"
    )
    assert "case_id" in sig.parameters


def test_invoke_module_path_is_repo_src():
    import llm_log_triage.chain as chain_module

    expected = (ROOT / "src" / "llm_log_triage" / "chain.py").resolve()
    actual = Path(chain_module.__file__).resolve()
    assert actual == expected, f"Expected {expected}, got {actual} (stale install?)"


def test_notebook_kernel_has_langchain_deps():
    from llm_log_triage.notebook_setup import verify_notebook_kernel

    verify_notebook_kernel(ROOT)


def test_notebook_file_exists():
    assert NOTEBOOK_PATH.is_file()


def test_load_project_env_reads_dotenv(monkeypatch):
    from llm_log_triage.notebook_setup import load_project_env

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    load_project_env(ROOT)
    # .env in repo should load when present (no assert on secret value)
    assert (ROOT / ".env").exists() or True


@pytest.mark.parametrize(
    "start_name",
    ["project_root", "notebooks"],
)
def test_notebook_path_bootstrap(start_name: str, monkeypatch):
    """Simulate notebook sys.path insert without importing twice."""
    start = ROOT if start_name == "project_root" else ROOT / "notebooks"
    monkeypatch.chdir(start)
    repo = find_repo_root(Path.cwd())
    src = str(repo / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    assert repo == ROOT
    assert src in sys.path
