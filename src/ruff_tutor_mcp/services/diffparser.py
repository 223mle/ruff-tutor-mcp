from __future__ import annotations

from typing import TypedDict


class DiffEntry(TypedDict):
    """Type definition for a diff entry."""

    before: str
    after: str


def parse_unified_diff(diff_output: str) -> dict[tuple[str, int], DiffEntry]:
    """Parse unified diff format output.

    Args:
        diff_output: Diff output.

    Returns:
        Dictionary of fix information keyed by (filename, row).

    """
    diff_map: dict[tuple[str, int], DiffEntry] = {}

    if not diff_output:
        return diff_map

    current_file: str | None = None
    current_line: int = 0

    for line in diff_output.splitlines():
        current_file, current_line = _process_diff_line(line, diff_map, current_file, current_line)

    return diff_map


def _process_diff_line(
    line: str,
    diff_map: dict[tuple[str, int], DiffEntry],
    current_file: str | None,
    current_line: int,
) -> tuple[str | None, int]:
    """Process a single line of diff.

    Args:
        line: A single line of diff.
        diff_map: Fix map (will be updated).
        current_file: Currently processing file.
        current_line: Current line number.

    Returns:
        Updated (current_file, current_line).

    """
    if line.startswith('--- '):
        file_path = line[4:].strip().removeprefix('a/')
        return file_path, current_line

    if line.startswith('@@ '):
        current_line = _extract_line_number(line)
        return current_file, current_line

    if line.startswith('-') and not line.startswith('---'):
        before = line[1:]
        if current_file is not None:
            diff_map[(current_file, current_line)] = {'before': before, 'after': ''}
        return current_file, current_line

    if line.startswith('+') and not line.startswith('+++'):
        after = line[1:]
        if current_file is not None and (current_file, current_line) in diff_map:
            diff_map[(current_file, current_line)]['after'] = after
        return current_file, current_line + 1

    if not line.startswith('\\'):
        return current_file, current_line + 1

    return current_file, current_line


def _extract_line_number(hunk_header: str) -> int:
    """Extract line number from hunk header.

    Args:
        hunk_header: String in @@ -10,5 +10,5 @@ format.

    Returns:
        Starting line number.

    """
    parts = hunk_header.split(' ')
    min_parts = 2
    if len(parts) >= min_parts:
        old_range = parts[1]
        if old_range.startswith('-'):
            line_info = old_range[1:].split(',')[0]
            return int(line_info)
    return 0
