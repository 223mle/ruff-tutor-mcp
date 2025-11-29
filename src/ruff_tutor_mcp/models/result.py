from __future__ import annotations

from pydantic import BaseModel

from ruff_tutor_mcp.models.rule import RuffRule
from ruff_tutor_mcp.models.violation import RuffViolation


class RuffAnalyzeResult(BaseModel):
    """Model representing Ruff analysis result."""

    violations: list[RuffViolation]
    rules: dict[str, RuffRule]

    @property
    def violation_count(self) -> int:
        """Return the total number of violations."""
        return len(self.violations)

    @property
    def unique_codes(self) -> list[str]:
        """Return unique error codes sorted."""
        return sorted({v.code for v in self.violations})

    @property
    def is_clean(self) -> bool:
        """Return whether there are no violations."""
        return len(self.violations) == 0
