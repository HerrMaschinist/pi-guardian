from __future__ import annotations

from sqlmodel import Session, SQLModel, create_engine

from app.memory import service
from app.models.agent_models import AgentRunRequest, AgentRunResponse, AgentStep, ToolCall, ToolResult


def test_memory_service_persists_runs_and_knowledge(monkeypatch):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    monkeypatch.setattr(service, "engine", engine)

    request = AgentRunRequest(agent_name="guardian_supervisor", prompt="Pruefe den Router")
    response = AgentRunResponse(
        agent_name="guardian_supervisor",
        success=True,
        final_answer="Alles stabil",
        used_model="llama3.1",
        run_id="run-123",
        steps=[
            AgentStep(
                step_number=1,
                action="tool_call",
                tool_call_or_response=ToolCall(
                    tool_name="system_status",
                    arguments={"scope": "router"},
                    reason="System prüfen",
                ),
                observation="Tool gestartet",
            ),
            AgentStep(
                step_number=1,
                action="tool_result",
                tool_call_or_response=ToolResult(
                    tool_name="system_status",
                    success=True,
                    output={"ok": True},
                ),
                observation="Ergebnis erhalten",
            ),
        ],
    )

    stored_run_id = service.record_agent_run(request, response)
    incident_id = service.create_incident(
        title="Router-Health",
        summary="kurze Analyse",
        severity="high",
        status="open",
        related_run_id=stored_run_id,
    )
    service.add_incident_finding(
        incident_id=incident_id or 0,
        source_type="run",
        source_ref=stored_run_id or "",
        finding_type="observation",
        content="Alles stabil",
        confidence=0.91,
    )
    knowledge_id = service.create_knowledge_entry(
        title="Router stabil",
        pattern="health ok",
        probable_cause="keine",
        recommended_checks="weiter prüfen",
        recommended_actions="keine Aktion",
        confidence=0.88,
        confirmed=True,
        source="test",
    )
    feedback_id = service.create_feedback_entry(
        related_run_id=stored_run_id,
        related_incident_id=incident_id,
        verdict="confirmed",
        comment="passt",
        created_by="tester",
    )

    with Session(engine) as session:
        runs = service.get_runs(session)
        run = service.get_run(session, stored_run_id or "")
        incidents = service.get_incidents(session)
        knowledge = service.get_knowledge_entries(session)
        feedback = service.get_feedback_entries(session)

    assert stored_run_id == "run-123"
    assert runs and runs[0].run_id == "run-123"
    assert run is not None
    assert run.final_answer == "Alles stabil"
    assert run.tool_calls[0].tool_name == "system_status"
    assert run.tool_results[0].output == {"ok": True}
    assert incidents and incidents[0].related_run_id == "run-123"
    assert incidents[0].findings[0].content == "Alles stabil"
    assert knowledge_id is not None
    assert knowledge and knowledge[0].confirmed is True
    assert feedback_id is not None
    assert feedback and feedback[0].verdict == "confirmed"
