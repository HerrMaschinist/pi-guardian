import logging
import os
from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

logger = logging.getLogger(__name__)

os.makedirs("data", exist_ok=True)

DATABASE_URL = "sqlite:///data/pi_guardian.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


def init_db() -> None:
    """Erstellt alle Tabellen beim App-Start (kein Alembic)."""
    SQLModel.metadata.create_all(engine)
    logger.info("Datenbankschema initialisiert: %s", DATABASE_URL)


def get_session() -> Generator[Session, None, None]:
    """FastAPI-Dependency: liefert eine DB-Session pro Request."""
    with Session(engine) as session:
        yield session
