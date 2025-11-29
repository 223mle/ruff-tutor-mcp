from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger

from ruff_tutor_mcp.commands import RuffCommand
from ruff_tutor_mcp.models import CodeFix, RuffAnalyzeResult, RuffRule, RuffViolation
from ruff_tutor_mcp.services.diffparser import parse_unified_diff


class RuffAnalyzer:
    """Class that executes Ruff commands and analyzes results."""

    def __init__(self, command: RuffCommand | None = None) -> None:
        self._command = command or RuffCommand()

    def analyze(self, path: str) -> RuffAnalyzeResult | None:
        """Analyze code at the specified path and return the result."""
        logger.info(f'Running ruff check on path: {path}')

        raw_violations = self._command.check(path)
        if raw_violations is None:
            return None

        violations = [self._to_violation(v) for v in raw_violations]
        rules = self._fetch_rules_for_violations(violations)

        return RuffAnalyzeResult(violations=violations, rules=rules)

    def generate_fixes(self, violations: list[RuffViolation], path: str) -> list[CodeFix]:
        """Generate fix information for violations."""
        diff_output = self._command.diff(path)
        diff_map = parse_unified_diff(diff_output)
        fixes: list[CodeFix] = []

        for violation in violations:
            before_line = self._read_source_line(violation.filename, violation.row)
            key = (violation.filename, violation.row)
            diff_info = diff_map.get(key)

            if diff_info is not None:
                fix = CodeFix(
                    filename=violation.filename,
                    row=violation.row,
                    before=before_line,
                    after=diff_info['after'],
                    violation_code=violation.code,
                    fixable=True,
                )
            else:
                fix = CodeFix(
                    filename=violation.filename,
                    row=violation.row,
                    before=before_line,
                    after=None,
                    violation_code=violation.code,
                    fixable=False,
                )

            fixes.append(fix)

        return fixes

    def _to_violation(self, raw: dict[str, Any]) -> RuffViolation:
        """Convert raw data to RuffViolation."""
        return RuffViolation(
            code=raw['code'],
            message=raw['message'],
            filename=raw['filename'],
            row=raw['location']['row'],
            col=raw['location']['column'],
            end_row=raw['end_location']['row'],
            end_col=raw['end_location']['column'],
            url=raw.get('url'),
        )

    def _fetch_rules_for_violations(self, violations: list[RuffViolation]) -> dict[str, RuffRule]:
        """Fetch rule explanations related to violations."""
        unique_codes = sorted({v.code for v in violations})
        rules: dict[str, RuffRule] = {}

        for code in unique_codes:
            explanation = self._command.rule(code)
            rules[code] = RuffRule(code=code, explanation=explanation)

        return rules

    def _read_source_line(self, filename: str, row: int) -> str:
        """Read the specified line from the source file."""
        try:
            file_path = Path(filename)
            lines = file_path.read_text(encoding='utf-8').splitlines()
            if 1 <= row <= len(lines):
                return lines[row - 1]
        except OSError:
            logger.warning(f'Failed to read file: {filename}')

        return ''
