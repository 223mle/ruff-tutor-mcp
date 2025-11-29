"""Tests for the config module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from ruff_tutor_mcp.config import (
    CONFIG_FILE_NAME,
    TutorConfig,
    TutorMode,
    load_config,
)

if TYPE_CHECKING:
    from pathlib import Path

# Test constants
DEFAULT_MAX_RETRY = 2
CUSTOM_MAX_RETRY = 5
FILE_MAX_RETRY = 3


class TestTutorMode:
    """Tests for TutorMode enum."""

    def test_mode_values(self) -> None:
        """Verify that mode values are correct."""
        assert TutorMode.BEGINNER.value == 'beginner'
        assert TutorMode.ADVANCED.value == 'advanced'
        assert TutorMode.AUTO.value == 'auto'


class TestTutorConfig:
    """Tests for TutorConfig model."""

    def test_default_config(self) -> None:
        """Verify that default configuration is correct."""
        config = TutorConfig.default()
        assert config.mode == TutorMode.BEGINNER
        assert config.max_retry == DEFAULT_MAX_RETRY

    def test_custom_config(self) -> None:
        """Verify that custom configuration is created correctly."""
        config = TutorConfig(mode=TutorMode.AUTO, max_retry=CUSTOM_MAX_RETRY)
        assert config.mode == TutorMode.AUTO
        assert config.max_retry == CUSTOM_MAX_RETRY

    def test_max_retry_validation(self) -> None:
        """Verify that max_retry validation works correctly."""
        with pytest.raises(ValidationError):
            TutorConfig(max_retry=0)
        with pytest.raises(ValidationError):
            TutorConfig(max_retry=11)


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_default_without_file(self, tmp_path: Path) -> None:
        """Verify that default config is returned when no config file exists."""
        config = load_config(tmp_path)
        assert config.mode == TutorMode.BEGINNER
        assert config.max_retry == DEFAULT_MAX_RETRY

    def test_load_from_file(self, tmp_path: Path) -> None:
        """Verify that configuration can be loaded from a file."""
        config_file = tmp_path / CONFIG_FILE_NAME
        config_file.write_text('mode = "advanced"\nmax_retry = 3\n')

        config = load_config(tmp_path)
        assert config.mode == TutorMode.ADVANCED
        assert config.max_retry == FILE_MAX_RETRY

    def test_mode_override(self, tmp_path: Path) -> None:
        """Verify that mode_override can override the mode."""
        config_file = tmp_path / CONFIG_FILE_NAME
        config_file.write_text('mode = "beginner"\n')

        config = load_config(tmp_path, mode_override='auto')
        assert config.mode == TutorMode.AUTO

    def test_invalid_mode_override_ignored(self, tmp_path: Path) -> None:
        """Verify that invalid mode_override is ignored."""
        config = load_config(tmp_path, mode_override='invalid')
        assert config.mode == TutorMode.BEGINNER

    def test_find_config_in_parent_dir(self, tmp_path: Path) -> None:
        """Verify that config file in parent directory is found."""
        config_file = tmp_path / CONFIG_FILE_NAME
        config_file.write_text('mode = "auto"\n')

        subdir = tmp_path / 'subdir'
        subdir.mkdir()

        config = load_config(subdir)
        assert config.mode == TutorMode.AUTO

    def test_invalid_toml_uses_default(self, tmp_path: Path) -> None:
        """Verify that default config is returned for invalid TOML file."""
        config_file = tmp_path / CONFIG_FILE_NAME
        config_file.write_text('invalid toml content {{{{')

        config = load_config(tmp_path)
        assert config.mode == TutorMode.BEGINNER
