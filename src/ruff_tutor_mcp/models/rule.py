from __future__ import annotations

from pydantic import BaseModel


class RuffRule(BaseModel):
    """Model representing Ruff rule explanation."""

    code: str
    explanation: str
