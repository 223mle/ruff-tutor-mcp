from __future__ import annotations

import uuid
from collections import Counter, OrderedDict
from dataclasses import dataclass, field

from loguru import logger

from ruff_tutor_mcp.models import ViolationRef

# (relative file path, rule code, stripped text of the violated line)
Fingerprint = tuple[str, str, str]

MAX_SESSIONS = 8


def make_fingerprint(file: str, code: str, line_text: str) -> Fingerprint:
    """Build a fingerprint that survives line-number shifts caused by edits."""
    return (file, code, line_text.strip())


@dataclass
class TrackedViolation:
    """A violation paired with its fingerprint for session tracking."""

    fingerprint: Fingerprint
    ref: ViolationRef


@dataclass
class Session:
    """State of one learning session (beginner/advanced modes only)."""

    id: str
    path: str
    mode: str
    max_retry: int
    initial: Counter[Fingerprint]
    refs: dict[Fingerprint, ViolationRef]
    attempts: int = 0
    last_fixed: int = 0
    last_remaining: int = 0

    def track_new(self, tracked: list[TrackedViolation]) -> None:
        """Fold newly appeared violations into the baseline so later checks treat them as remaining."""
        for item in tracked:
            self.initial[item.fingerprint] += 1
            self.refs.setdefault(item.fingerprint, item.ref)

    @property
    def rules_covered(self) -> list[str]:
        return sorted({code for _, code, _ in self.initial})


@dataclass
class SessionStore:
    """In-memory session store with FIFO eviction."""

    max_sessions: int = MAX_SESSIONS
    _sessions: OrderedDict[str, Session] = field(default_factory=OrderedDict)

    def create(self, path: str, mode: str, max_retry: int, tracked: list[TrackedViolation]) -> Session:
        session = Session(
            id=uuid.uuid4().hex[:8],
            path=path,
            mode=mode,
            max_retry=max_retry,
            initial=Counter(item.fingerprint for item in tracked),
            refs={item.fingerprint: item.ref for item in tracked},
            last_remaining=len(tracked),
        )
        self._sessions[session.id] = session
        while len(self._sessions) > self.max_sessions:
            evicted_id, _ = self._sessions.popitem(last=False)
            logger.debug(f'Evicted oldest session: {evicted_id}')
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def remove(self, session_id: str) -> Session | None:
        return self._sessions.pop(session_id, None)


def split_progress(
    initial: Counter[Fingerprint],
    refs: dict[Fingerprint, ViolationRef],
    current: list[Fingerprint],
) -> tuple[list[ViolationRef], list[bool]]:
    """Partition current violations against the session baseline.

    Returns (fixed_refs, remaining_flags) where remaining_flags aligns with
    `current`: True means the violation existed at session start (remaining),
    False means it newly appeared. Multiset semantics handle duplicate
    fingerprints (e.g. identical lines violating the same rule).
    """
    budget: Counter[Fingerprint] = Counter(initial)
    remaining_flags: list[bool] = []
    for fingerprint in current:
        if budget[fingerprint] > 0:
            budget[fingerprint] -= 1
            remaining_flags.append(True)
        else:
            remaining_flags.append(False)

    fixed: list[ViolationRef] = []
    for fingerprint, count in budget.items():
        ref = refs.get(fingerprint)
        if ref is not None and count > 0:
            fixed.extend([ref] * count)

    return fixed, remaining_flags
