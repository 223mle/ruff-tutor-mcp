from __future__ import annotations

import json
import subprocess
from typing import TYPE_CHECKING

from ruff_tutor_mcp.ruff_runner import RuffRunner

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def completed(stdout: str, stderr: str = '', returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=['ruff'], returncode=returncode, stdout=stdout, stderr=stderr)


CHECK_OUTPUT = json.dumps(
    [
        {
            'code': 'E712',
            'message': 'Avoid equality comparisons to `True`',
            'filename': '/tmp/sample.py',
            'location': {'row': 2, 'column': 4},
            'end_location': {'row': 2, 'column': 13},
            'url': 'https://docs.astral.sh/ruff/rules/true-false-comparison',
            'fix': {
                'applicability': 'unsafe',
                'message': 'Replace with `x`',
                'edits': [
                    {
                        'content': 'x',
                        'location': {'row': 2, 'column': 4},
                        'end_location': {'row': 2, 'column': 13},
                    }
                ],
            },
        },
        {
            'code': None,
            'message': 'SyntaxError: unexpected token',
            'filename': '/tmp/broken.py',
            'location': {'row': 1, 'column': 1},
            'end_location': {'row': 1, 'column': 2},
        },
    ]
)


class TestCheck:
    def test_parses_violations_with_fix(self, monkeypatch: pytest.MonkeyPatch) -> None:
        runner = RuffRunner()
        monkeypatch.setattr(runner, '_run', lambda args: completed(CHECK_OUTPUT))
        violations = runner.check('.')
        assert violations is not None
        assert violations[0].code == 'E712'
        assert violations[0].fix is not None
        assert violations[0].fix.edits[0].content == 'x'
        assert violations[0].fix.edits[0].end_col == 13

    def test_null_code_becomes_syntax_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        runner = RuffRunner()
        monkeypatch.setattr(runner, '_run', lambda args: completed(CHECK_OUTPUT))
        violations = runner.check('.')
        assert violations is not None
        assert violations[1].code == 'syntax-error'
        assert violations[1].fix is None

    def test_unparsable_output_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        runner = RuffRunner()
        monkeypatch.setattr(runner, '_run', lambda args: completed('not json', stderr='boom'))
        assert runner.check('.') is None


class TestRule:
    def test_parses_and_caches(self, monkeypatch: pytest.MonkeyPatch) -> None:
        runner = RuffRunner()
        calls: list[list[str]] = []

        def fake_run(args: list[str]) -> subprocess.CompletedProcess[str]:
            calls.append(args)
            return completed(
                json.dumps(
                    {
                        'name': 'true-false-comparison',
                        'code': 'E712',
                        'summary': 'Avoid equality comparisons to `True`',
                        'explanation': '## What it does\n...',
                        'fix_availability': 'Always',
                    }
                )
            )

        monkeypatch.setattr(runner, '_run', fake_run)
        first = runner.rule('E712')
        second = runner.rule('E712')
        assert first is not None
        assert first.name == 'true-false-comparison'
        assert first.url == 'https://docs.astral.sh/ruff/rules/true-false-comparison/'
        assert second is first
        assert len(calls) == 1

    def test_unknown_rule_returns_none_and_caches(self, monkeypatch: pytest.MonkeyPatch) -> None:
        runner = RuffRunner()
        calls: list[list[str]] = []

        def fake_run(args: list[str]) -> subprocess.CompletedProcess[str]:
            calls.append(args)
            return completed('', stderr='invalid rule', returncode=2)

        monkeypatch.setattr(runner, '_run', fake_run)
        assert runner.rule('ZZZ999') is None
        assert runner.rule('ZZZ999') is None
        assert len(calls) == 1


class TestIntegration:
    """Tests against the real bundled ruff binary."""

    def test_check_real_file(self, tmp_path: Path) -> None:
        (tmp_path / 'ruff.toml').write_text('[lint]\nselect = ["F401", "E712"]\n')
        (tmp_path / 'sample.py').write_text('import os\nx = 1\nif x == True:\n    pass\n')
        violations = RuffRunner().check(str(tmp_path))
        assert violations is not None
        assert sorted(v.code for v in violations) == ['E712', 'F401']

    def test_rule_real_lookup(self) -> None:
        doc = RuffRunner().rule('F401')
        assert doc is not None
        assert doc.name == 'unused-import'
        assert 'unused' in doc.explanation.lower()
