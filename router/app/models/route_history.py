from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class RouteHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    request_id: str = Field(index=True, unique=True)
    prompt_preview: str
    model: str | None = None
    success: bool = False
    error_code: str | None = None
    client_name: str | None = None
    duration_ms: int | None = None
    fairness_review_attempted: bool = False
    fairness_review_used: bool = False
    fairness_risk: str = Field(default="unknown")
    fairness_review_override: bool = False
    fairness_threshold: str | None = None
    fairness_reasons: str = Field(default="[]")
    fairness_notes: str = Field(default="[]")
    created_at: datetime = Field(default_factory=datetime.now)
