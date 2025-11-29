from __future__ import annotations

from pydantic import BaseModel

from ruff_tutor_mcp.models import CodeFix, RuffAnalyzeResult, RuffRule, RuffViolation
from ruff_tutor_mcp.templates import INSTRUCTION_CLEAN, get_instruction_for_mode


class TutorResponse(BaseModel):
    """Response model returned by the MCP tool."""

    status: str
    mode: str
    violation_count: int
    violations: list[RuffViolation]
    rules: dict[str, RuffRule]
    fixes: list[CodeFix]
    instruction: str
    retry_count: int | None = None


class TutorService:
    """Service for building learning support responses."""

    def create_response(
        self,
        result: RuffAnalyzeResult,
        fixes: list[CodeFix],
        mode: str,
    ) -> TutorResponse:
        """Generate a response according to the mode.

        Args:
            result: Ruff analysis result.
            fixes: List of fix information.
            mode: Learning mode.

        Returns:
            TutorResponse instance.

        """
        return TutorResponse(
            status='violations_found',
            mode=mode,
            violation_count=result.violation_count,
            violations=result.violations,
            rules=result.rules,
            fixes=fixes,
            instruction=get_instruction_for_mode(mode),
        )

    def clean_response(self, mode: str) -> TutorResponse:
        """Generate a response when there are no violations.

        Args:
            mode: Learning mode.

        Returns:
            TutorResponse instance.

        """
        return TutorResponse(
            status='clean',
            mode=mode,
            violation_count=0,
            violations=[],
            rules={},
            fixes=[],
            instruction=INSTRUCTION_CLEAN,
        )

    def error_response(self, message: str, mode: str) -> TutorResponse:
        """Generate a response on error.

        Args:
            message: Error message.
            mode: Learning mode.

        Returns:
            TutorResponse instance.

        """
        return TutorResponse(
            status='error',
            mode=mode,
            violation_count=0,
            violations=[],
            rules={},
            fixes=[],
            instruction=message,
        )

    def retry_response(
        self,
        result: RuffAnalyzeResult,
        fixes: list[CodeFix],
        retry_count: int,
    ) -> TutorResponse:
        """Generate a response on retry.

        Args:
            result: Ruff analysis result.
            fixes: List of fix information.
            retry_count: Current retry count.

        Returns:
            TutorResponse instance.

        """
        return TutorResponse(
            status='retry',
            mode='beginner',
            violation_count=result.violation_count,
            violations=result.violations,
            rules=result.rules,
            fixes=fixes,
            instruction='Some violations still remain. Here are the Before/After examples. Please try again.',
            retry_count=retry_count + 1,
        )

    def max_retry_response(
        self,
        result: RuffAnalyzeResult,
        fixes: list[CodeFix],
    ) -> TutorResponse:
        """Generate a response when maximum retry is reached.

        Args:
            result: Ruff analysis result.
            fixes: List of fix information.

        Returns:
            TutorResponse instance.

        """
        return TutorResponse(
            status='max_retry',
            mode='auto',
            violation_count=result.violation_count,
            violations=result.violations,
            rules=result.rules,
            fixes=fixes,
            instruction='You have tried multiple times. Here are the Before/After examples. '
            'Please auto-fix the remaining violations.',
        )
