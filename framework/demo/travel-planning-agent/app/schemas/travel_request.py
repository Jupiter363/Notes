from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class TravelPreference(str, Enum):
    food = "美食"
    relaxed = "轻松"
    nature = "自然风光"
    culture = "历史文化"
    shopping = "购物"
    parent_child = "亲子"
    photography = "拍照"


class TravelRequest(BaseModel):
    destination: Optional[str] = Field(default=None, description="目的地城市或地区")
    start_date: Optional[str] = Field(default=None, description="出发日期或时间范围，例如 6 月底")
    days: Optional[int] = Field(default=None, ge=1, le=30, description="旅行天数")
    budget: Optional[float] = Field(default=None, ge=0, description="总预算，单位元")
    preferences: List[str] = Field(default_factory=list, description="旅行偏好")
    companions: Optional[str] = Field(default=None, description="同行人，例如独自、情侣、朋友、亲子")
    departure_city: Optional[str] = Field(default=None, description="出发城市，可选")
    pace: Optional[str] = Field(default=None, description="旅行节奏，例如轻松、适中、紧凑")
