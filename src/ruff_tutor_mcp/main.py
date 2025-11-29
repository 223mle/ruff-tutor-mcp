"""Ruff Tutor MCP Server - Code review and learning support tool."""

from __future__ import annotations

from loguru import logger
from mcp.server.fastmcp import FastMCP

from ruff_tutor_mcp.config import load_config
from ruff_tutor_mcp.services import RuffAnalyzer, TutorService

MCP_SERVER_NAME = 'Ruff Tutor'
mcp = FastMCP(MCP_SERVER_NAME)

_analyzer = RuffAnalyzer()
_tutor_service = TutorService()


@mcp.tool()
def review_code_and_teach(path: str = '.', mode: str | None = None) -> str:
    """Check code at the specified path with Ruff and generate learning material.

    Args:
        path: Path to check (default: current directory).
        mode: Learning mode (beginner, advanced, auto). Refers to config file if not specified.

    Returns:
        Structured data in JSON format (violations, rules, fixes, instruction).

    """
    config = load_config(path, mode_override=mode)
    current_mode = config.mode.value
    logger.info(f'Using mode: {current_mode}')

    result = _analyzer.analyze(path)

    if result is None:
        logger.warning('Failed to analyze code')
        response = _tutor_service.error_response('Failed to parse ruff output.', mode=current_mode)
        return response.model_dump_json(indent=2)

    if result.is_clean:
        logger.info('No ruff errors found')
        return _tutor_service.clean_response(mode=current_mode).model_dump_json(indent=2)

    logger.info(f'Found {result.violation_count} ruff errors')
    fixes = _analyzer.generate_fixes(result.violations, path)
    return _tutor_service.create_response(result, fixes=fixes, mode=current_mode).model_dump_json(indent=2)


@mcp.tool()
def verify_fix(
    path: str = '.',
    previous_codes: list[str] | None = None,
    retry_count: int = 0,
) -> str:
    """Verify user's fix and show Before/After if violations still remain.

    Args:
        path: Path to check (default: current directory).
        previous_codes: List of violation codes detected previously.
        retry_count: Retry count.

    Returns:
        Structured data in JSON format.

    """
    config = load_config(path)
    current_mode = config.mode.value

    result = _analyzer.analyze(path)

    if result is None:
        logger.warning('Failed to analyze code')
        response = _tutor_service.error_response('Failed to parse ruff output.', mode=current_mode)
        return response.model_dump_json(indent=2)

    if result.is_clean:
        logger.info('All violations fixed!')
        return _tutor_service.clean_response(mode=current_mode).model_dump_json(indent=2)

    remaining_codes = {v.code for v in result.violations}
    previous_set = set(previous_codes) if previous_codes else set()
    still_remaining = remaining_codes & previous_set
    fixes = _analyzer.generate_fixes(result.violations, path)

    if not still_remaining:
        logger.info('Previous violations fixed, but new ones found')
        return _tutor_service.create_response(result, fixes=fixes, mode=current_mode).model_dump_json(indent=2)

    if retry_count >= config.max_retry:
        logger.info('Max retry reached, showing Before/After and suggesting auto-fix')
        return _tutor_service.max_retry_response(result, fixes=fixes).model_dump_json(indent=2)

    logger.info(f'Violations still remain, retry {retry_count + 1}')
    return _tutor_service.retry_response(result, fixes=fixes, retry_count=retry_count).model_dump_json(indent=2)


def main() -> None:
    """Start the MCP server."""
    mcp.run()


if __name__ == '__main__':
    main()
