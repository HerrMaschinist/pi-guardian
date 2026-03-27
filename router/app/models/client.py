from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Client(SQLModel, table=True):
    """Persistierter Client-Eintrag in der SQLite-Datenbank."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str = ""
    active: bool = True
    allowed_ip: str = "192.168.50.0/24"
    # Kommasepariert gespeichert, als list[str] über die API exponiert
    allowed_routes: str = "/route,/health"
    api_key: str = Field(unique=True)
    created_at: datetime = Field(default_factory=datetime.now)

    def allowed_routes_list(self) -> list[str]:
        return [r.strip() for r in self.allowed_routes.split(",") if r.strip()]


# ── Pydantic-Schemas (kein table=True) ────────────────────────────────────────

class ClientCreate(SQLModel):
    name: str
    description: str = ""
    active: bool = True
    allowed_ip: str = "192.168.50.0/24"
    allowed_routes: list[str] = Field(default=["/route", "/health"])


class ClientRead(SQLModel):
    id: int
    name: str
    description: str
    active: bool
    allowed_ip: str
    allowed_routes: list[str]
    # Nur bei POST (Erstellung) gefüllt; bei GET leer
    api_key: str
    created_at: datetime


class ClientUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None
    allowed_ip: Optional[str] = None
    allowed_routes: Optional[list[str]] = None
