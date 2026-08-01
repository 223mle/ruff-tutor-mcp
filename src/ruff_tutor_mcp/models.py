from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class FixEdit(BaseModel):
    """A single text edit from ruff's native fix data (1-based rows/columns)."""

    content: str
    row: int
    col: int
    end_row: int
    end_col: int


class RuffFix(BaseModel):
    """Fix metadata attached to a violation by ruff."""

    applicability: str
    message: str | None = None
    edits: list[FixEdit] = Field(default_factory=list)


class RuffViolation(BaseModel):
    """A violation reported by `ruff check --output-format=json`."""

    code: str
    message: str
    filename: str
    row: int
    col: int
    end_row: int
    end_col: int
    url: str | None = None
    fix: RuffFix | None = None


class RuleDoc(BaseModel):
    """Full rule documentation from `ruff rule --output-format=json`."""

    code: str
    name: str
    summary: str
    explanation: str
    fix_availability: str
    url: str | None = None


class ViolationDetail(BaseModel):
    """A single violation prepared for teaching (with source context)."""

    file: str
    row: int
    col: int
    message: str
    before: str
    after: str | None = None
    fixable: bool = False
    # ruff's fix applicability ("safe" / "unsafe" / ...); unsafe fixes may change behavior
    fix_applicability: str | None = None


class ViolationGroup(BaseModel):
    """Violations grouped by rule code, with a one-line rule summary.

    Full rule documentation is intentionally omitted; clients fetch it on
    demand via the `explain_rule` tool.
    """

    code: str
    rule_name: str
    summary: str
    url: str | None = None
    count: int
    violations: list[ViolationDetail]


class ViolationRef(BaseModel):
    """A lightweight reference to a violation (used to report fixed ones)."""

    file: str
    row: int
    code: str
    message: str


class ReviewResponse(BaseModel):
    """Result of the `review_code` tool.

    In auto mode this is a one-shot report. In beginner/advanced mode it also
    carries a `session_id` for the `check_my_fix` learning loop.
    """

    status: Literal['clean', 'violations_found', 'error']
    mode: str
    total: int
    groups: list[ViolationGroup] = Field(default_factory=list)
    session_id: str | None = None
    max_retry: int | None = None
    instruction: str


class Progress(BaseModel):
    """Result of the `check_my_fix` tool."""

    verdict: Literal['passed', 'keep_trying', 'answer_revealed', 'session_not_found', 'error']
    attempts: int
    max_retry: int
    fixed: list[ViolationRef] = Field(default_factory=list)
    remaining: list[ViolationGroup] = Field(default_factory=list)
    new: list[ViolationGroup] = Field(default_factory=list)
    instruction: str


class SessionSummary(BaseModel):
    """Result of the `end_session` tool."""

    session_id: str
    fixed_count: int
    remaining_count: int
    attempts: int
    rules_covered: list[str] = Field(default_factory=list)
    instruction: str
