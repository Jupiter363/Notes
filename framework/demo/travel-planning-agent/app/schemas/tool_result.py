from pydantic import BaseModel, Field
from typing import Optional


class ToolResult(BaseModel):
    data: dict | list
    source: str
    updated_at: Optional[str] = None
    confidence: str = Field(description="mock/high/medium/low")
    error: Optional[str] = None
