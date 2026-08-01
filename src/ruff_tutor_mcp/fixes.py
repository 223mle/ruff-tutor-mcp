from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ruff_tutor_mcp.models import FixEdit, RuffViolation


def source_line(source: str, row: int) -> str:
    """Return the text of the given 1-based line, or '' when out of range."""
    return _line_at(_normalize(source).split('\n'), row)


def render_fix(source: str, violation: RuffViolation) -> tuple[str, str | None]:
    """Render before/after snippets for a violation from ruff's native fix edits.

    Returns (before, after). `after` is None when ruff provides no fix.
    The snippets cover the full lines spanned by the edits, so multi-line
    fixes and line deletions render correctly.
    """
    source = _normalize(source)
    lines = source.split('\n')

    if violation.fix is None or not violation.fix.edits:
        return _line_at(lines, violation.row), None

    edits = violation.fix.edits
    start_row = min(edit.row for edit in edits)
    end_row = max(edit.end_row for edit in edits)

    before = '\n'.join(lines[start_row - 1 : end_row])

    new_lines = _apply_edits(source, edits).split('\n')
    delta = len(new_lines) - len(lines)
    after = '\n'.join(new_lines[start_row - 1 : end_row + delta])

    return before, after


def _normalize(source: str) -> str:
    r"""Normalize line endings to '\n' so ruff's row/col coordinates map cleanly.

    Lines are always derived via split('\n') (never str.splitlines, which also
    splits on characters ruff does not treat as line breaks, e.g. form feed)
    so that line indexing stays consistent with `_line_starts`.
    """
    return source.replace('\r\n', '\n').replace('\r', '\n')


def _line_at(lines: list[str], row: int) -> str:
    if 1 <= row <= len(lines):
        return lines[row - 1]
    return ''


def _line_starts(source: str) -> list[int]:
    starts = [0]
    for index, char in enumerate(source):
        if char == '\n':
            starts.append(index + 1)
    return starts


def _offset(starts: list[int], source_length: int, row: int, col: int) -> int:
    if row - 1 < len(starts):
        return min(starts[row - 1] + col - 1, source_length)
    return source_length


def _apply_edits(source: str, edits: list[FixEdit]) -> str:
    starts = _line_starts(source)
    length = len(source)
    spans = sorted(
        (
            (
                _offset(starts, length, edit.row, edit.col),
                _offset(starts, length, edit.end_row, edit.end_col),
                edit.content,
            )
            for edit in edits
        ),
        reverse=True,
    )
    result = source
    for span_start, span_end, content in spans:
        result = result[:span_start] + content + result[span_end:]
    return result
