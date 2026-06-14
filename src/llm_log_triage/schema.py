"""Pydantic models for LLM log triage I/O.

This file defines the contract between the LLM and everything else:
- TriageInput: what callers pass in (CLI, Streamlit, tests)
- TriageOutput: structured JSON the LLM must return (validated by Pydantic)
- Enums constrain severity/category so evals can exact-match golden labels
"""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Severity(str, Enum):
    SEV1 = "SEV1"
    SEV2 = "SEV2"
    SEV3 = "SEV3"
    SEV4 = "SEV4"
    UNKNOWN = "unknown"


class Category(str, Enum):
    CONNECTIVITY = "connectivity"
    RESOURCE = "resource"
    AUTH = "auth"
    CONFIG = "config"
    DEPENDENCY = "dependency"
    UNKNOWN = "unknown"


class TriageInput(BaseModel):
    log_text: str
    service_name: str | None = None

    @field_validator("log_text", mode="before")
    @classmethod
    def strip_log(cls, v: str) -> str:
        return v if v is None else str(v).strip()


class TriageOutput(BaseModel):
    severity: Severity
    category: Category
    likely_cause: str = Field(..., min_length=1)
    suggested_action: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_lines: list[str] = Field(default_factory=list)


PROMPT_VERSIONS = Literal["v1", "v2", "v3"]
