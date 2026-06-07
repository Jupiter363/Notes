from pydantic import BaseModel, Field
from typing import List


class ReflectionResult(BaseModel):
    need_revision: bool
    score: int = Field(ge=1, le=10)
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    blocking_issues: List[str] = Field(default_factory=list)
    accepted_as_final: bool = False
