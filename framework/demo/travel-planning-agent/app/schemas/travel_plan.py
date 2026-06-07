from pydantic import BaseModel, Field
from typing import List, Optional


class Activity(BaseModel):
    time_slot: str = Field(description="morning/afternoon/evening")
    title: str
    location: Optional[str] = None
    reason: str = Field(description="为什么这样安排")
    estimated_cost: float = 0
    duration_hours: Optional[float] = None
    transport_note: Optional[str] = None
    risk_note: Optional[str] = None


class DayPlan(BaseModel):
    day: int
    theme: str
    activities: List[Activity]
    daily_estimated_cost: float
    pace_level: str = Field(description="relaxed/normal/tight")
    notes: List[str] = Field(default_factory=list)


class TravelPlan(BaseModel):
    destination: str
    total_days: int
    total_budget: float
    days: List[DayPlan]
    total_estimated_cost: float
    budget_status: str = Field(description="within_budget/slightly_over/over_budget/unknown")
    preference_match_notes: List[str] = Field(default_factory=list)
    risk_notes: List[str] = Field(default_factory=list)
    data_limitations: List[str] = Field(default_factory=list)
