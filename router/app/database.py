import logging
import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine, select

from app.config import BASE_DIR
from app.router.admin_client import ensure_admin_client
from app.router.model_registry import sync_model_registry
from app.router.model_pull import reset_stale_pull_jobs
from app.memory import models as _memory_models  # noqa: F401
from app.models import model_registry as _model_registry_models  # noqa: F401
from app.models import model_pull as _model_pull_models  # noqa: F401

logger = logging.getLogger(__name__)

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = Path(os.getenv("PI_GUARDIAN_DB_PATH", DATA_DIR / "pi_guardian.db"))
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


def init_db() -> None:
    """Erstellt alle Tabellen beim App-Start (kein Alembic)."""
    SQLModel.metadata.create_all(engine)
    _ensure_route_history_columns()
    _bootstrap_reference_data()
    _bootstrap_admin_client()
    _bootstrap_model_registry()
    reset_stale_pull_jobs()
    logger.info("Datenbankschema initialisiert: %s", DATABASE_URL)


def _ensure_route_history_columns() -> None:
    """Ergänzt fehlende Spalten für bestehende SQLite-Datenbanken."""
    expected_columns = {
        "fairness_review_attempted": "ALTER TABLE routehistory ADD COLUMN fairness_review_attempted BOOLEAN NOT NULL DEFAULT 0",
        "fairness_review_used": "ALTER TABLE routehistory ADD COLUMN fairness_review_used BOOLEAN NOT NULL DEFAULT 0",
        "fairness_risk": "ALTER TABLE routehistory ADD COLUMN fairness_risk VARCHAR NOT NULL DEFAULT 'unknown'",
        "fairness_review_override": "ALTER TABLE routehistory ADD COLUMN fairness_review_override BOOLEAN NOT NULL DEFAULT 0",
        "fairness_threshold": "ALTER TABLE routehistory ADD COLUMN fairness_threshold VARCHAR",
        "fairness_reasons": "ALTER TABLE routehistory ADD COLUMN fairness_reasons VARCHAR NOT NULL DEFAULT '[]'",
        "fairness_notes": "ALTER TABLE routehistory ADD COLUMN fairness_notes VARCHAR NOT NULL DEFAULT '[]'",
    }

    with engine.begin() as conn:
        existing = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(routehistory)")).fetchall()
        }
        for column_name, ddl in expected_columns.items():
            if column_name not in existing:
                conn.execute(text(ddl))
                logger.info("Route-History-Spalte ergänzt: %s", column_name)


def _bootstrap_reference_data() -> None:
    try:
        from app.persistence.reference_data import bootstrap_reference_data
    except Exception as exc:
        logger.warning("Referenzdaten-Bootstrap konnte nicht geladen werden: %s", exc)
        return

    try:
        with Session(engine) as session:
            bootstrap_reference_data(session)
    except Exception as exc:
        logger.warning("Referenzdaten-Bootstrap fehlgeschlagen: %s", exc)


def _bootstrap_admin_client() -> None:
    with Session(engine) as session:
        ensure_admin_client(session)


def _bootstrap_model_registry() -> None:
    with Session(engine) as session:
        sync_model_registry(session)


def get_session() -> Generator[Session, None, None]:
    """FastAPI-Dependency: liefert eine DB-Session pro Request."""
    with Session(engine) as session:
        yield session
