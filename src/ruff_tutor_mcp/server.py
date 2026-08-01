"""Ruff Tutor MCP Server - learn Python best practices through ruff violations."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import groupby
from pathlib import Path
from typing import Literal

from loguru import logger
from mcp.server.fastmcp import FastMCP

from ruff_tutor_mcp import instructions
from ruff_tutor_mcp.config import TutorMode, load_config
from ruff_tutor_mcp.fixes import render_fix, source_line
from ruff_tutor_mcp.models import (
    Progress,
    ReviewResponse,
    RuffViolation,
    RuleDoc,
    SessionSummary,
    ViolationDetail,
    ViolationGroup,
    ViolationRef,
)
from ruff_tutor_mcp.ruff_runner import RuffRunner
from ruff_tutor_mcp.sessions import SessionStore, TrackedViolation, make_fingerprint, split_progress

MCP_SERVER_NAME = 'Ruff Tutor'

mcp = FastMCP(MCP_SERVER_NAME)

_runner = RuffRunner()
_store = SessionStore()


@dataclass
class _Inspected:
    """A violation enriched with source context for teaching."""

    violation: RuffViolation
    file: str
    line: str
    before: str
    after: str | None

    @property
    def fingerprint(self) -> tuple[str, str, str]:
        return make_fingerprint(self.file, self.violation.code, self.line)

    @property
    def ref(self) -> ViolationRef:
        return ViolationRef(
            file=self.file,
            row=self.violation.row,
            code=self.violation.code,
            message=self.violation.message,
        )


def _scan_base(path: str) -> Path:
    resolved = Path(path).resolve()
    return resolved.parent if resolved.is_file() else resolved


def _relative(filename: str, base: Path) -> str:
    try:
        return str(Path(filename).resolve().relative_to(base))
    except ValueError:
        return filename


def _inspect(path: str) -> list[_Inspected] | None:
    """Run ruff and enrich each violation with before/after snippets."""
    violations = _runner.check(path)
    if violations is None:
        return None

    base = _scan_base(path)
    source_cache: dict[str, str] = {}
    inspected: list[_Inspected] = []

    for violation in violations:
        source = source_cache.get(violation.filename)
        if source is None:
            try:
                source = Path(violation.filename).read_text(encoding='utf-8')
            except OSError:
                logger.warning(f'Failed to read file: {violation.filename}')
                source = ''
            source_cache[violation.filename] = source
        before, after = render_fix(source, violation)
        inspected.append(
            _Inspected(
                violation=violation,
                file=_relative(violation.filename, base),
                line=source_line(source, violation.row),
                before=before,
                after=after,
            )
        )

    return inspected


def _build_groups(items: list[_Inspected], include_fixes: bool) -> list[ViolationGroup]:
    """Group violations by rule code with a one-line rule summary."""
    groups: list[ViolationGroup] = []
    for code, grouped in groupby(sorted(items, key=lambda i: i.violation.code), key=lambda i: i.violation.code):
        members = list(grouped)
        doc = _runner.rule(code)
        first = members[0].violation
        # ruff rule summaries may be message templates ("... argument `{name}`");
        # fall back to the concrete message when placeholders are present
        rule_summary = doc.summary if doc else ''
        groups.append(
            ViolationGroup(
                code=code,
                rule_name=doc.name if doc else '',
                summary=rule_summary if rule_summary and '{' not in rule_summary else first.message,
                url=doc.url if doc else first.url,
                count=len(members),
                violations=[
                    ViolationDetail(
                        file=item.file,
                        row=item.violation.row,
                        col=item.violation.col,
                        message=item.violation.message,
                        before=item.before,
                        after=item.after if include_fixes else None,
                        fixable=item.after is not None,
                        fix_applicability=item.violation.fix.applicability if item.violation.fix else None,
                    )
                    for item in members
                ],
            )
        )
    return groups


@mcp.tool()
def review_code(path: str = '.', mode: str | None = None) -> ReviewResponse:
    """Check code at the given path with ruff and build a teaching report.

    In auto mode (default) this is a one-shot report: explain, then auto-fix.
    In beginner/advanced mode it starts a learning session - the user fixes the
    code themselves and progress is verified via `check_my_fix(session_id)`.

    Args:
        path: File or directory to check (default: current directory).
        mode: Learning mode (beginner, advanced, auto). Falls back to the
            project's .ruff-tutor.toml, then to auto.

    """
    config = load_config(path, mode_override=mode)
    current_mode = config.mode.value
    logger.info(f'Reviewing {path} in {current_mode} mode')

    items = _inspect(path)
    if items is None:
        return ReviewResponse(status='error', mode=current_mode, total=0, instruction=instructions.ERROR)
    if not items:
        return ReviewResponse(status='clean', mode=current_mode, total=0, instruction=instructions.CLEAN)

    if config.mode is TutorMode.AUTO:
        return ReviewResponse(
            status='violations_found',
            mode=current_mode,
            total=len(items),
            groups=_build_groups(items, include_fixes=True),
            instruction=instructions.AUTO,
        )

    session = _store.create(
        path=path,
        mode=current_mode,
        max_retry=config.max_retry,
        tracked=[TrackedViolation(fingerprint=item.fingerprint, ref=item.ref) for item in items],
    )
    logger.info(f'Started session {session.id} with {len(items)} violations')
    return ReviewResponse(
        status='violations_found',
        mode=current_mode,
        total=len(items),
        groups=_build_groups(items, include_fixes=config.mode is TutorMode.BEGINNER),
        session_id=session.id,
        max_retry=config.max_retry,
        instruction=instructions.lesson_instruction(current_mode),
    )


@mcp.tool()
def check_my_fix(session_id: str) -> Progress:
    """Re-check the session's code and report learning progress.

    Reports which violations the user fixed, which remain, and which are new.
    The server tracks attempts; after max_retry attempts the correct fixes are
    revealed.

    Args:
        session_id: Session ID returned by `review_code`.

    """
    session = _store.get(session_id)
    if session is None:
        return Progress(
            verdict='session_not_found',
            attempts=0,
            max_retry=0,
            instruction=instructions.SESSION_NOT_FOUND,
        )

    items = _inspect(session.path)
    if items is None:
        return Progress(
            verdict='error',
            attempts=session.attempts,
            max_retry=session.max_retry,
            instruction=instructions.ERROR,
        )

    session.attempts += 1

    if not items:
        fixed, _ = split_progress(session.initial, session.refs, [])
        session.last_fixed = len(fixed)
        session.last_remaining = 0
        logger.info(f'Session {session.id}: all violations fixed')
        return Progress(
            verdict='passed',
            attempts=session.attempts,
            max_retry=session.max_retry,
            fixed=fixed,
            instruction=instructions.PASSED,
        )

    fixed, remaining_flags = split_progress(
        session.initial,
        session.refs,
        [item.fingerprint for item in items],
    )
    remaining_items = [item for item, is_old in zip(items, remaining_flags, strict=True) if is_old]
    new_items = [item for item, is_old in zip(items, remaining_flags, strict=True) if not is_old]

    session.last_fixed = len(fixed)
    session.last_remaining = len(remaining_items) + len(new_items)
    session.track_new([TrackedViolation(fingerprint=item.fingerprint, ref=item.ref) for item in new_items])

    verdict: Literal['answer_revealed', 'keep_trying']
    if session.attempts >= session.max_retry:
        verdict, include_fixes = 'answer_revealed', True
        instruction = instructions.ANSWER_REVEALED
    else:
        verdict, include_fixes = 'keep_trying', session.mode == TutorMode.BEGINNER.value
        instruction = instructions.keep_trying_instruction(session.mode)

    logger.info(
        f'Session {session.id}: attempt {session.attempts}/{session.max_retry}, '
        f'{len(fixed)} fixed / {len(remaining_items)} remaining / {len(new_items)} new'
    )
    return Progress(
        verdict=verdict,
        attempts=session.attempts,
        max_retry=session.max_retry,
        fixed=fixed,
        remaining=_build_groups(remaining_items, include_fixes=include_fixes),
        new=_build_groups(new_items, include_fixes=include_fixes),
        instruction=instruction,
    )


@mcp.tool()
def explain_rule(code: str) -> RuleDoc:
    """Fetch the full documentation for a ruff rule (e.g. "E712").

    Use this for rules worth teaching in depth; the `explanation` field
    contains the full rationale with examples.

    Args:
        code: Ruff rule code.

    """
    doc = _runner.rule(code)
    if doc is None:
        return RuleDoc(
            code=code,
            name='',
            summary='',
            explanation=f'No ruff rule found for code: {code}',
            fix_availability='',
        )
    return doc


@mcp.tool()
def end_session(session_id: str) -> SessionSummary:
    """Close a learning session and get a summary of the results.

    Args:
        session_id: Session ID returned by `review_code`.

    """
    session = _store.remove(session_id)
    if session is None:
        return SessionSummary(
            session_id=session_id,
            fixed_count=0,
            remaining_count=0,
            attempts=0,
            instruction=instructions.SESSION_NOT_FOUND,
        )
    return SessionSummary(
        session_id=session_id,
        fixed_count=session.last_fixed,
        remaining_count=session.last_remaining,
        attempts=session.attempts,
        rules_covered=session.rules_covered,
        instruction=instructions.SESSION_ENDED,
    )


def main() -> None:
    """Start the MCP server."""
    mcp.run()


if __name__ == '__main__':
    main()
