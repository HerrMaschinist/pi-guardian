from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

from sqlmodel import Session

from app.database import engine
from app.models.agent_models import AgentDefinition
from app.persistence.reference_data import load_agent_definitions, save_agent_definitions

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]
AGENT_STORE_PATH = BASE_DIR / "data" / "agents.json"


def load_agent_records() -> list[AgentDefinition]:
    try:
        with Session(engine) as session:
            records = load_agent_definitions(session)
            if records:
                return records
    except Exception as exc:
        logger.warning("Agent store konnte nicht aus SQLite geladen werden: %s", exc)

    if not AGENT_STORE_PATH.exists():
        return []

    import json

    try:
        payload = json.loads(AGENT_STORE_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Legacy agent store konnte nicht gelesen werden: %s", exc)
        return []

    if not isinstance(payload, dict):
        return []

    records = payload.get("agents", [])
    if not isinstance(records, list):
        return []

    loaded: list[AgentDefinition] = []
    for item in records:
        if not isinstance(item, dict):
            continue
        try:
            loaded.append(AgentDefinition.model_validate(item))
        except Exception as exc:
            logger.warning("Ungültiger Agenten-Datensatz übersprungen: %s", exc)
    return loaded


def save_agent_records(agents: Iterable[AgentDefinition]) -> None:
    definitions = sorted(agents, key=lambda a: a.name)
    try:
        with Session(engine) as session:
            save_agent_definitions(session, definitions)
        return
    except Exception as exc:
        logger.warning("Agent store konnte nicht in SQLite gespeichert werden: %s", exc)

    AGENT_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    import json

    payload = {
        "version": 1,
        "agents": [agent.model_dump(mode="json") for agent in definitions],
    }
    tmp_path = AGENT_STORE_PATH.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(AGENT_STORE_PATH)
