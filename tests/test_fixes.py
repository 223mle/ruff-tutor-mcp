from __future__ import annotations

from ruff_tutor_mcp.fixes import render_fix, source_line
from ruff_tutor_mcp.models import FixEdit, RuffFix, RuffViolation


def make_violation(row: int, edits: list[FixEdit] | None = None) -> RuffViolation:
    fix = RuffFix(applicability='safe', edits=edits) if edits is not None else None
    return RuffViolation(
        code='X999',
        message='test violation',
        filename='sample.py',
        row=row,
        col=1,
        end_row=row,
        end_col=2,
        fix=fix,
    )


class TestSourceLine:
    def test_returns_line_text(self) -> None:
        assert source_line('a\nb\nc\n', 2) == 'b'

    def test_out_of_range_returns_empty(self) -> None:
        assert source_line('a\n', 5) == ''

    def test_normalizes_crlf(self) -> None:
        assert source_line('a\r\nb\r\n', 2) == 'b'


class TestRenderFix:
    def test_no_fix_returns_line_and_none(self) -> None:
        violation = make_violation(row=2)
        before, after = render_fix('a\nif x == True:\nc\n', violation)
        assert before == 'if x == True:'
        assert after is None

    def test_single_line_replacement(self) -> None:
        source = 'a = 1\nif x == True:\n    pass\n'
        # replace "x == True" (row 2, cols 4-13) with "x"
        edits = [FixEdit(content='x', row=2, col=4, end_row=2, end_col=13)]
        before, after = render_fix(source, make_violation(row=2, edits=edits))
        assert before == 'if x == True:'
        assert after == 'if x:'

    def test_multi_line_deletion(self) -> None:
        source = 'import os\nx = 1\n'
        # delete line 1 including its newline (F401-style edit)
        edits = [FixEdit(content='', row=1, col=1, end_row=2, end_col=1)]
        before, after = render_fix(source, make_violation(row=1, edits=edits))
        assert before == 'import os\nx = 1'
        assert after == 'x = 1'

    def test_insertion_adds_lines(self) -> None:
        source = 'import os\ndef f():\n    pass\n'
        # I001-style: rewrite the import block adding blank lines
        edits = [FixEdit(content='import os\n\n\n', row=1, col=1, end_row=2, end_col=1)]
        before, after = render_fix(source, make_violation(row=1, edits=edits))
        assert before == 'import os\ndef f():'
        assert after == 'import os\n\n\ndef f():'

    def test_multiple_edits_applied_together(self) -> None:
        source = 'a = (1,\n     2,\n     3)\n'
        edits = [
            FixEdit(content='[', row=1, col=5, end_row=1, end_col=6),
            FixEdit(content=']', row=3, col=7, end_row=3, end_col=8),
        ]
        before, after = render_fix(source, make_violation(row=1, edits=edits))
        assert before == 'a = (1,\n     2,\n     3)'
        assert after == 'a = [1,\n     2,\n     3]'

    def test_edit_beyond_file_end_is_clamped(self) -> None:
        source = 'x = 1'
        edits = [FixEdit(content='', row=1, col=1, end_row=99, end_col=1)]
        before, after = render_fix(source, make_violation(row=1, edits=edits))
        assert before == 'x = 1'
        assert after == ''
