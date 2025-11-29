from __future__ import annotations

import tomllib
from enum import Enum
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import BaseModel, Field, ValidationError

CONFIG_FILE_NAME = '.ruff-tutor.toml'


class TutorMode(str, Enum):
    """Enum representing learning mode."""

    BEGINNER = 'beginner'
    ADVANCED = 'advanced'
    AUTO = 'auto'


class TutorConfig(BaseModel):
    """Model representing ruff_tutor configuration."""

    mode: TutorMode = Field(default=TutorMode.AUTO, description='Learning mode')
    max_retry: int = Field(default=2, ge=1, le=10, description='Maximum retry count in advanced mode')

    @classmethod
    def default(cls) -> TutorConfig:
        """Return default configuration."""
        return cls()


def _find_config_file(start_path: Path) -> Path | None:
    """Search for config file by traversing parent directories from the specified path.

    Args:
        start_path: Starting path for search.

    Returns:
        Path to config file, or None if not found.

    """
    current = start_path.resolve()

    if current.is_file():
        current = current.parent

    for parent in [current, *current.parents]:
        config_path = parent / CONFIG_FILE_NAME
        if config_path.exists():
            logger.debug(f'Found config file: {config_path}')
            return config_path

    return None


def _parse_toml(path: Path) -> dict[str, Any]:
    """Parse TOML file.

    Args:
        path: Path to TOML file.

    Returns:
        Parsed dictionary.

    """
    with path.open('rb') as f:
        return tomllib.load(f)


def load_config(path: str | Path | None = None, mode_override: str | None = None) -> TutorConfig:
    """Load configuration.

    Priority:
    1. mode_override parameter
    2. Config file (.ruff-tutor.toml)
    3. Default values

    Args:
        path: Starting path for search (current directory if not specified).
        mode_override: Value to override the mode.

    Returns:
        Loaded configuration.

    """
    start_path = Path(path) if path else Path.cwd()
    config_file = _find_config_file(start_path)

    if config_file is None:
        logger.debug('No config file found, using defaults')
        config = TutorConfig.default()
    else:
        try:
            data = _parse_toml(config_file)
            config = TutorConfig.model_validate(data)
            logger.info(f'Loaded config from {config_file}')
        except (ValidationError, tomllib.TOMLDecodeError, OSError) as e:
            logger.warning(f'Failed to parse config file: {e}, using defaults')
            config = TutorConfig.default()

    if mode_override is not None:
        try:
            config.mode = TutorMode(mode_override)
            logger.debug(f'Mode overridden to: {mode_override}')
        except ValueError:
            logger.warning(f'Invalid mode override: {mode_override}, keeping {config.mode}')

    return config
