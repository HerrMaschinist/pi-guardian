from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


ModelRole = str


class ModelRecord(SQLModel, table=True):
    """Persistenter Modellkatalog für den Router."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: str = ""
    role: ModelRole = Field(default="registered", index=True)
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ModelCreate(SQLModel):
    name: str
    description: str = ""
    enabled: bool = True


class ModelRead(SQLModel):
    id: int
    name: str
    description: str
    role: ModelRole
    enabled: bool
    created_at: datetime
    updated_at: datetime


class ModelUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
