from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ruff_tutor_mcp import server

if TYPE_CHECKING:
    from pathlib import Path

DIRTY_CODE = 'import os\nx = 1\nif x == True:\n    pass\n'
PARTIALLY_FIXED_CODE = 'x = 1\nif x == True:\n    pass\n'
CLEAN_CODE = 'x = 1\nif x:\n    pass\n'


@pytest.fixture
def project(tmp_path: Path) -> Path:
    # 対象プロジェクト側の ruff 設定が尊重されることも兼ねて、ルールを固定する
    (tmp_path / 'ruff.toml').write_text('[lint]\nselect = ["F401", "E712"]\n')
    (tmp_path / 'sample.py').write_text(DIRTY_CODE)
    return tmp_path


class TestReviewCode:
    def test_auto_mode_returns_one_shot_report(self, project: Path) -> None:
        response = server.review_code(str(project), mode='auto')
        assert response.status == 'violations_found'
        assert response.mode == 'auto'
        assert response.session_id is None
        assert response.total == 2
        assert sorted(g.code for g in response.groups) == ['E712', 'F401']
        fixables = [v for g in response.groups for v in g.violations if v.fixable]
        assert all(v.after is not None for v in fixables)

    def test_beginner_mode_starts_session_with_fixes(self, project: Path) -> None:
        response = server.review_code(str(project), mode='beginner')
        assert response.session_id is not None
        assert response.max_retry is not None
        e712 = next(g for g in response.groups if g.code == 'E712')
        assert e712.violations[0].after == 'if x:'
        assert e712.violations[0].before == 'if x == True:'

    def test_advanced_mode_never_includes_fixes(self, project: Path) -> None:
        response = server.review_code(str(project), mode='advanced')
        assert response.session_id is not None
        assert all(v.after is None for g in response.groups for v in g.violations)
        # fixable であることは伝わる（答えは見せない）
        assert any(v.fixable for g in response.groups for v in g.violations)

    def test_clean_code(self, tmp_path: Path) -> None:
        (tmp_path / 'ruff.toml').write_text('[lint]\nselect = ["F401", "E712"]\n')
        (tmp_path / 'sample.py').write_text(CLEAN_CODE)
        response = server.review_code(str(tmp_path), mode='beginner')
        assert response.status == 'clean'
        assert response.session_id is None

    def test_mode_from_config_file(self, project: Path) -> None:
        (project / '.ruff-tutor.toml').write_text('mode = "advanced"\n')
        response = server.review_code(str(project))
        assert response.mode == 'advanced'


class TestCheckMyFix:
    def test_partial_fix_reports_progress(self, project: Path) -> None:
        lesson = server.review_code(str(project), mode='beginner')
        assert lesson.session_id is not None
        (project / 'sample.py').write_text(PARTIALLY_FIXED_CODE)

        progress = server.check_my_fix(lesson.session_id)
        assert progress.verdict == 'keep_trying'
        assert progress.attempts == 1
        assert [ref.code for ref in progress.fixed] == ['F401']
        assert [g.code for g in progress.remaining] == ['E712']
        assert progress.new == []
        # beginner の keep_trying では引き続き after を見せる
        assert progress.remaining[0].violations[0].after is not None

    def test_advanced_keep_trying_hides_fixes(self, project: Path) -> None:
        lesson = server.review_code(str(project), mode='advanced')
        assert lesson.session_id is not None
        (project / 'sample.py').write_text(PARTIALLY_FIXED_CODE)

        progress = server.check_my_fix(lesson.session_id)
        assert progress.verdict == 'keep_trying'
        assert all(v.after is None for g in progress.remaining for v in g.violations)

    def test_full_fix_passes(self, project: Path) -> None:
        lesson = server.review_code(str(project), mode='beginner')
        assert lesson.session_id is not None
        (project / 'sample.py').write_text(CLEAN_CODE)

        progress = server.check_my_fix(lesson.session_id)
        assert progress.verdict == 'passed'
        assert sorted(ref.code for ref in progress.fixed) == ['E712', 'F401']
        assert progress.remaining == []

    def test_answer_revealed_after_max_retry(self, project: Path) -> None:
        (project / '.ruff-tutor.toml').write_text('mode = "advanced"\nmax_retry = 2\n')
        lesson = server.review_code(str(project))
        assert lesson.session_id is not None

        first = server.check_my_fix(lesson.session_id)
        assert first.verdict == 'keep_trying'

        second = server.check_my_fix(lesson.session_id)
        assert second.verdict == 'answer_revealed'
        # リトライ上限に達したら advanced でも答えを開示する
        fixables = [v for g in second.remaining for v in g.violations if v.fixable]
        assert fixables
        assert all(v.after is not None for v in fixables)

    def test_new_violation_is_reported_and_tracked(self, project: Path) -> None:
        lesson = server.review_code(str(project), mode='beginner')
        assert lesson.session_id is not None
        # F401 は直したが、新たな E712 違反を書いてしまった
        (project / 'sample.py').write_text('x = 1\nif x == True:\n    pass\nif x == False:\n    pass\n')

        progress = server.check_my_fix(lesson.session_id)
        assert progress.verdict == 'keep_trying'
        assert [g.code for g in progress.new] == ['E712']

        # 次のチェックでは new がベースラインに編入され remaining として扱われる
        second = server.check_my_fix(lesson.session_id)
        assert second.new == []

    def test_unknown_session(self) -> None:
        progress = server.check_my_fix('does-not-exist')
        assert progress.verdict == 'session_not_found'
        assert 'review_code' in progress.instruction


class TestEndSession:
    def test_summary_after_pass(self, project: Path) -> None:
        lesson = server.review_code(str(project), mode='beginner')
        assert lesson.session_id is not None
        (project / 'sample.py').write_text(CLEAN_CODE)
        server.check_my_fix(lesson.session_id)

        summary = server.end_session(lesson.session_id)
        assert summary.fixed_count == 2
        assert summary.remaining_count == 0
        assert summary.rules_covered == ['E712', 'F401']
        # 終了後は取得できない
        assert server.end_session(lesson.session_id).rules_covered == []


class TestExplainRule:
    def test_known_rule(self) -> None:
        doc = server.explain_rule('E712')
        assert doc.name == 'true-false-comparison'
        assert doc.explanation

    def test_unknown_rule(self) -> None:
        doc = server.explain_rule('ZZZ999')
        assert 'No ruff rule found' in doc.explanation
