from __future__ import annotations

import json
import subprocess
from typing import Any

from loguru import logger
from ruff.__main__ import find_ruff_bin

from ruff_tutor_mcp.models import FixEdit, RuffFix, RuffViolation, RuleDoc

RUFF_DOCS_BASE = 'https://docs.astral.sh/ruff/rules'

# ruff reports syntax errors with "code": null
SYNTAX_ERROR_CODE = 'syntax-error'


class RuffRunner:
    """Runs the bundled ruff binary and parses its JSON output.

    The target project's own ruff configuration (pyproject.toml / ruff.toml)
    is still respected because ruff resolves it from the checked path.
    """

    def __init__(self) -> None:
        self._ruff_bin = find_ruff_bin()
        self._rule_cache: dict[str, RuleDoc | None] = {}

    def check(self, path: str) -> list[RuffViolation] | None:
        """Run `ruff check` and return violations, or None on unparsable output."""
        result = self._run(['check', path, '--output-format=json', '--no-cache'])
        try:
            raw = json.loads(result.stdout)
        except json.JSONDecodeError:
            logger.warning(f'Failed to parse ruff check output: {result.stderr.strip()}')
            return None
        return [self._to_violation(item) for item in raw]

    def rule(self, code: str) -> RuleDoc | None:
        """Fetch rule documentation via `ruff rule`, cached per process."""
        if code in self._rule_cache:
            return self._rule_cache[code]

        result = self._run(['rule', code, '--output-format=json'])
        doc: RuleDoc | None
        try:
            raw = json.loads(result.stdout)
            name = raw.get('name', '')
            doc = RuleDoc(
                code=code,
                name=name,
                summary=raw.get('summary', ''),
                explanation=raw.get('explanation', ''),
                fix_availability=raw.get('fix_availability', ''),
                url=f'{RUFF_DOCS_BASE}/{name}/' if name else None,
            )
        except json.JSONDecodeError:
            logger.warning(f'Failed to fetch rule documentation for {code}: {result.stderr.strip()}')
            doc = None

        self._rule_cache[code] = doc
        return doc

    def _run(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        command = [self._ruff_bin, *args]
        logger.debug(f'Running: {" ".join(command)}')
        return subprocess.run(  # noqa: S603
            command,
            capture_output=True,
            text=True,
            check=False,
        )

    def _to_violation(self, raw: dict[str, Any]) -> RuffViolation:
        fix: RuffFix | None = None
        raw_fix = raw.get('fix')
        if raw_fix:
            fix = RuffFix(
                applicability=raw_fix.get('applicability', 'unknown'),
                message=raw_fix.get('message'),
                edits=[
                    FixEdit(
                        content=edit['content'],
                        row=edit['location']['row'],
                        col=edit['location']['column'],
                        end_row=edit['end_location']['row'],
                        end_col=edit['end_location']['column'],
                    )
                    for edit in raw_fix.get('edits', [])
                ],
            )
        return RuffViolation(
            code=raw.get('code') or SYNTAX_ERROR_CODE,
            message=raw['message'],
            filename=raw['filename'],
            row=raw['location']['row'],
            col=raw['location']['column'],
            end_row=raw['end_location']['row'],
            end_col=raw['end_location']['column'],
            url=raw.get('url'),
            fix=fix,
        )
