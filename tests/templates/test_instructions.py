from __future__ import annotations

from ruff_tutor_mcp.templates import get_instruction_for_mode


class TestGetInstructionForMode:
    """Tests for get_instruction_for_mode function."""

    def test_beginner_mode(self) -> None:
        """Verify that beginner mode instruction is returned."""
        instruction = get_instruction_for_mode('beginner')
        assert 'Before | After' in instruction
        assert 'Do NOT auto-fix' in instruction

    def test_advanced_mode(self) -> None:
        """Verify that advanced mode instruction is returned."""
        instruction = get_instruction_for_mode('advanced')
        assert 'Do NOT show Before/After' in instruction

    def test_auto_mode(self) -> None:
        """Verify that auto mode instruction is returned."""
        instruction = get_instruction_for_mode('auto')
        assert 'automatically fix' in instruction

    def test_unknown_mode_returns_beginner(self) -> None:
        """Verify that unknown mode falls back to beginner instruction."""
        instruction = get_instruction_for_mode('unknown')
        beginner_instruction = get_instruction_for_mode('beginner')
        assert instruction == beginner_instruction
