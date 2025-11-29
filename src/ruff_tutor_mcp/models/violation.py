from __future__ import annotations

from pydantic import BaseModel


class RuffViolation(BaseModel):
    """Model representing a violation detected by Ruff."""

    code: str
    message: str
    filename: str
    row: int
    col: int
    end_row: int
    end_col: int
    url: str | None = None

    @property
    def location(self) -> str:
        """Return the violation location as a string."""
        return f'{self.filename}:{self.row}:{self.col}'
