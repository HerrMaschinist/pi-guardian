from datetime import datetime
from typing import Optional

from pydantic import ConfigDict
from sqlmodel import Field, SQLModel


ModelPullStatus = str


class ModelPullJob(SQLModel, table=True):
    model_config = ConfigDict(protected_namespaces=())

    id: Optional[int] = Field(default=None, primary_key=True)
    model_name: str = Field(index=True)
    status: ModelPullStatus = Field(default="queued", index=True)
    progress_message: str = ""
    progress_percent: int | None = None
    requested_by: str | None = None
    result_summary: str | None = None
    error_message: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    started_at: datetime | None = None
    finished_at: datetime | None = None


class ModelPullCreate(SQLModel):
    model_config = ConfigDict(protected_namespaces=())

    model_name: str


class ModelPullRead(SQLModel):
    model_config = ConfigDict(protected_namespaces=())

    id: int
    model_name: str
    status: ModelPullStatus
    progress_message: str
    progress_percent: int | None = None
    requested_by: str | None = None
    result_summary: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
