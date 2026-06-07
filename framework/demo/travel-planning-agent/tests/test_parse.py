"""测试需求解析功能。"""

import pytest
from app.schemas.travel_request import TravelRequest


class TestTravelRequest:
    def test_create_minimal_request(self):
        req = TravelRequest(destination="成都", days=3, budget=3000, preferences=["美食", "轻松"])
        assert req.destination == "成都"
        assert req.days == 3
        assert req.budget == 3000
        assert "美食" in req.preferences

    def test_create_empty_request(self):
        req = TravelRequest()
        assert req.destination is None
        assert req.days is None
        assert req.preferences == []

    def test_days_validation(self):
        with pytest.raises(Exception):
            TravelRequest(destination="成都", days=0, budget=3000)

        with pytest.raises(Exception):
            TravelRequest(destination="成都", days=31, budget=3000)

    def test_budget_validation(self):
        with pytest.raises(Exception):
            TravelRequest(destination="成都", days=3, budget=-100)

    def test_model_dump(self):
        req = TravelRequest(destination="成都", days=3, budget=3000, preferences=["美食"])
        d = req.model_dump()
        assert d["destination"] == "成都"
        assert d["days"] == 3
