"""Notebook bootstrap — load .env and verify kernel has project deps."""

from __future__ import annotations

import sys
from pathlib import Path

REQUIRED_PACKAGES = (
    "langchain_openai",
    "langchain_anthropic",
    "langchain_core",
    "dotenv",
)


def find_repo_root(start: Path | None = None) -> Path:
    """Locate llm-log-triage root whether cwd is repo/ or notebooks/."""
    here = (start or Path.cwd()).resolve()
    if (here / "src" / "llm_log_triage" / "chain.py").exists():
        return here
    if (here.parent / "src" / "llm_log_triage" / "chain.py").exists():
        return here.parent
    raise RuntimeError(
        f"Cannot find repo root from {here}. "
        "Start Jupyter from llm-log-triage/ or notebooks/."
    )


def load_project_env(root: Path) -> None:
    """Load repo-root .env (Jupyter cwd is often notebooks/)."""
    from dotenv import load_dotenv

    load_dotenv(root / ".env")


def verify_notebook_kernel(root: Path) -> None:
    """Fail fast if Jupyter is not using the project venv."""
    missing = [name for name in REQUIRED_PACKAGES if not _can_import(name)]
    if not missing:
        return

    venv_python = root / ".venv" / "bin" / "python"
    in_project_venv = venv_python.exists() and Path(sys.executable).resolve() == venv_python.resolve()

    lines = [
        f"Missing packages: {', '.join(missing)}",
        f"Python executable: {sys.executable}",
    ]
    if venv_python.exists():
        lines.append(f"Project venv:      {venv_python}")
        lines.append(f"Using project venv: {in_project_venv}")
    lines.extend(
        [
            "",
            "Fix (pick one):",
            "  1. Kernel → Change kernel → Python (.venv) for this repo",
            f"  2. Terminal: cd {root} && python -m ipykernel install --user --name=llm-log-triage",
            f"  3. In notebook: %pip install -e \"{root}[dev,obs]\"  then Restart Kernel",
        ]
    )
    raise ModuleNotFoundError("\n".join(lines))


def _can_import(module_name: str) -> bool:
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False
