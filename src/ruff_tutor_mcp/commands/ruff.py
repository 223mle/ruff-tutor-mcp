from __future__ import annotations

import json
import subprocess
from typing import Any

from loguru import logger


class RuffCommand:
    def check(self, path: str) -> list[dict[str, Any]] | None:
        """Execute ruff check --output-format=json."""
        logger.debug(f'Running ruff check on: {path}')
        result = subprocess.run(  # noqa: S603
            ['uv', 'run', 'ruff', 'check', path, '--output-format=json'],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
        )
        return self._parse_json(result.stdout)

    def rule(self, code: str) -> str:
        """Execute ruff rule <code> to fetch rule explanation."""
        logger.debug(f'Fetching rule explanation for: {code}')
        result = subprocess.run(  # noqa: S603
            ['uv', 'run', 'ruff', 'rule', code],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout

    def diff(self, path: str) -> str:
        """Execute ruff check --fix --diff to get fix diff."""
        logger.debug(f'Getting fix diff for: {path}')
        result = subprocess.run(  # noqa: S603
            ['uv', 'run', 'ruff', 'check', path, '--fix', '--diff'],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout

    def _parse_json(self, stdout: str) -> list[dict[str, Any]] | None:
        """Parse JSON output."""
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            logger.warning('Failed to parse ruff output as JSON')
            return None
