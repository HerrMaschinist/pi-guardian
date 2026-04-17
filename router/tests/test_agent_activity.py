from datetime import datetime, timedelta

from sqlmodel import Session, SQLModel, create_engine

from app.agents.activity import get_agent_activity_map
from app.memory.models import AgentRunRecord


def _session() -> Session:
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_get_agent_activity_map_uses_latest_run_per_agent():
    now = datetime.now()

    with _session() as session:
        session.add(
            AgentRunRecord(
                run_id="run-old",
                agent_name="guardian_supervisor",
                input="Alte Anfrage",
                used_model="qwen-old",
                success=True,
                final_answer="Alte Antwort",
                started_at=now - timedelta(minutes=10),
                finished_at=now - timedelta(minutes=9, seconds=55),
            )
        )
        session.add(
            AgentRunRecord(
                run_id="run-new",
                agent_name="guardian_supervisor",
                input="Bitte prüfe den aktuellen Dienststatus und gib eine knappe Bewertung aus.",
                used_model="qwen-new",
                success=False,
                final_answer="Fehler gefunden",
                started_at=now - timedelta(minutes=1),
                finished_at=now - timedelta(seconds=30),
            )
        )
        session.add(
            AgentRunRecord(
                run_id="run-other",
                agent_name="service_operator",
                input="Statusabfrage",
                used_model="qwen-service",
                success=True,
                final_answer="Alles grün",
                started_at=now - timedelta(minutes=2),
                finished_at=now - timedelta(minutes=2) + timedelta(seconds=2),
            )
        )
        session.commit()

        activity = get_agent_activity_map(session)

    assert activity["guardian_supervisor"].last_run_id == "run-new"
    assert activity["guardian_supervisor"].last_status == "failed"
    assert activity["guardian_supervisor"].last_model == "qwen-new"
    assert activity["guardian_supervisor"].last_activity.startswith("Bitte prüfe den aktuellen Dienststatus")
    assert activity["guardian_supervisor"].last_duration_ms == 30000
    assert activity["service_operator"].last_status == "success"
