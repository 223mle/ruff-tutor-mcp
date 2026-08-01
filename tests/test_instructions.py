from __future__ import annotations

from ruff_tutor_mcp import instructions


class TestLessonInstruction:
    def test_beginner_shows_before_after(self) -> None:
        text = instructions.lesson_instruction('beginner')
        assert 'Before | After' in text
        assert 'do NOT edit the files yourself' in text
        assert 'check_my_fix' in text

    def test_advanced_hides_fixes(self) -> None:
        text = instructions.lesson_instruction('advanced')
        assert 'NO fix examples' in text
        assert 'Do NOT reveal' in text
        assert 'check_my_fix' in text

    def test_auto_applies_fixes(self) -> None:
        assert 'apply the fixes to the code automatically' in instructions.AUTO


class TestKeepTryingInstruction:
    def test_beginner_variant(self) -> None:
        text = instructions.keep_trying_instruction('beginner')
        assert 'try again' in text
        assert 'do NOT reveal' not in text.lower()

    def test_advanced_variant_stays_hidden(self) -> None:
        text = instructions.keep_trying_instruction('advanced')
        assert 'conceptual hints only' in text
