from __future__ import annotations

from pydantic import BaseModel


class CodeFix(BaseModel):
    """Model representing fix information for a violation."""

    filename: str
    row: int
    before: str
    after: str | None = None
    violation_code: str
    fixable: bool = False
