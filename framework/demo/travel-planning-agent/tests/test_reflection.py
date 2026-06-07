"""测试 Reflection 相关 schema 和逻辑。"""

from app.schemas.reflection import ReflectionResult
from app.graph.routers import route_after_reflection


class TestReflectionResult:
    def test_create_reflection(self):
        r = ReflectionResult(
            need_revision=True,
            score=6,
            issues=["预算超支"],
            suggestions=["减少高端餐厅"],
            blocking_issues=[],
            accepted_as_final=False,
        )
        assert r.need_revision is True
        assert r.score == 6
        assert len(r.issues) == 1

    def test_accepted_as_final(self):
        r = ReflectionResult(
            need_revision=False,
            score=9,
            issues=[],
            suggestions=[],
            blocking_issues=[],
            accepted_as_final=True,
        )
        assert r.accepted_as_final is True

    def test_score_range(self):
        import pytest
        with pytest.raises(Exception):
            ReflectionResult(need_revision=False, score=0)
        with pytest.raises(Exception):
            ReflectionResult(need_revision=False, score=11)


class TestRouteAfterReflection:
    def test_accepted_as_final_goes_to_output(self):
        state = {
            "reflection": {"need_revision": True, "accepted_as_final": True},
            "revision_count": 0,
            "max_revision_count": 2,
        }
        assert route_after_reflection(state) == "final_output"

    def test_need_revision_and_within_limit(self):
        state = {
            "reflection": {"need_revision": True, "accepted_as_final": False},
            "revision_count": 0,
            "max_revision_count": 2,
        }
        assert route_after_reflection(state) == "revise_plan"

    def test_need_revision_exceeds_limit(self):
        state = {
            "reflection": {"need_revision": True, "accepted_as_final": False},
            "revision_count": 2,
            "max_revision_count": 2,
        }
        assert route_after_reflection(state) == "final_output"

    def test_no_revision_needed(self):
        state = {
            "reflection": {"need_revision": False, "accepted_as_final": False},
            "revision_count": 0,
            "max_revision_count": 2,
        }
        assert route_after_reflection(state) == "final_output"
