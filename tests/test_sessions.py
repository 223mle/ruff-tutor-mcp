from __future__ import annotations

from collections import Counter

from ruff_tutor_mcp.models import ViolationRef
from ruff_tutor_mcp.sessions import (
    SessionStore,
    TrackedViolation,
    make_fingerprint,
    split_progress,
)


def tracked(file: str, code: str, line: str) -> TrackedViolation:
    return TrackedViolation(
        fingerprint=make_fingerprint(file, code, line),
        ref=ViolationRef(file=file, row=1, code=code, message=f'{code} violation'),
    )


class TestMakeFingerprint:
    def test_strips_line_text(self) -> None:
        assert make_fingerprint('a.py', 'E712', '  if x == True:  ') == ('a.py', 'E712', 'if x == True:')

    def test_survives_line_shift(self) -> None:
        # the fingerprint has no line number, so moving the line keeps it equal
        assert make_fingerprint('a.py', 'E712', 'if x == True:') == make_fingerprint(
            'a.py', 'E712', '    if x == True:'
        )


class TestSplitProgress:
    def test_all_fixed(self) -> None:
        items = [tracked('a.py', 'F401', 'import os')]
        initial = _counter(items)
        fixed, flags = split_progress(
            initial=initial,
            refs={t.fingerprint: [t.ref] for t in items},
            current=[],
        )
        assert len(fixed) == 1
        assert fixed[0].code == 'F401'
        assert flags == []
        assert initial == _counter(items)  # input is not mutated

    def test_remaining_and_new(self) -> None:
        old = tracked('a.py', 'E712', 'if x == True:')
        new = tracked('a.py', 'F821', 'y = undefined')
        fixed, flags = split_progress(
            initial=_counter([old]),
            refs={old.fingerprint: [old.ref]},
            current=[old.fingerprint, new.fingerprint],
        )
        assert fixed == []
        assert flags == [True, False]

    def test_duplicate_fingerprints_use_multiset_semantics(self) -> None:
        # two identical lines violating the same rule; one gets fixed
        item = tracked('a.py', 'E712', 'if x == True:')
        fixed, flags = split_progress(
            initial=_counter([item, item]),
            refs={item.fingerprint: [item.ref, item.ref]},
            current=[item.fingerprint],
        )
        assert len(fixed) == 1
        assert flags == [True]


class TestSessionStore:
    def test_create_and_get(self) -> None:
        store = SessionStore()
        session = store.create(path='.', mode='beginner', max_retry=2, tracked=[tracked('a.py', 'F401', 'x')])
        assert store.get(session.id) is session
        assert session.last_remaining == 1

    def test_get_unknown_returns_none(self) -> None:
        assert SessionStore().get('nope') is None

    def test_remove(self) -> None:
        store = SessionStore()
        session = store.create(path='.', mode='beginner', max_retry=2, tracked=[])
        assert store.remove(session.id) is session
        assert store.get(session.id) is None

    def test_eviction_drops_oldest(self) -> None:
        store = SessionStore(max_sessions=2)
        first = store.create(path='.', mode='beginner', max_retry=2, tracked=[])
        second = store.create(path='.', mode='beginner', max_retry=2, tracked=[])
        third = store.create(path='.', mode='beginner', max_retry=2, tracked=[])
        assert store.get(first.id) is None
        assert store.get(second.id) is not None
        assert store.get(third.id) is not None

    def test_track_new_folds_into_baseline(self) -> None:
        store = SessionStore()
        session = store.create(path='.', mode='beginner', max_retry=2, tracked=[])
        new = tracked('a.py', 'F821', 'y = undefined')
        session.track_new([new])
        assert session.initial[new.fingerprint] == 1
        assert session.refs[new.fingerprint] == [new.ref]
        assert session.rules_covered == ['F821']


def _counter(items: list[TrackedViolation]) -> Counter[tuple[str, str, str]]:
    return Counter(t.fingerprint for t in items)
