from __future__ import annotations

from app.models.agent_models import AgentDefinition, AgentRunState
from app.actions.registry import list_action_names
from app.skills.registry import list_skill_names
from app.tools.registry import list_tools


def _render_history(state: AgentRunState) -> str:
    if not state.context_history:
        return "- Keine vorherigen Schritte."

    lines: list[str] = []
    for step in state.context_history:
        payload = step.tool_call_or_response
        lines.append(
            f"- Schritt {step.step_number} [{step.action}]: {payload} | Beobachtung: {step.observation or '-'}"
        )
    return "\n".join(lines)


def _render_tool_catalog(agent: AgentDefinition) -> str:
    lines: list[str] = []
    for tool in list_tools():
        if tool.name not in agent.allowed_tools:
            continue
        lines.append(f"- {tool.name}: {tool.description}")
    return "\n".join(lines) if lines else "- Keine Tools registriert."


def _render_skill_catalog(agent: AgentDefinition) -> str:
    lines: list[str] = []
    for skill_name in list_skill_names():
        if skill_name not in agent.settings.policy.allowed_skills:
            continue
        lines.append(f"- {skill_name}")
    return "\n".join(lines) if lines else "- Keine Skills registriert."


def _render_action_catalog(agent: AgentDefinition) -> str:
    lines: list[str] = []
    for action_name in list_action_names():
        if action_name not in agent.settings.policy.allowed_actions:
            continue
        lines.append(f"- {action_name}")
    return "\n".join(lines) if lines else "- Keine Actions registriert."


def build_system_prompt(agent: AgentDefinition) -> str:
    settings = agent.settings
    policy = settings.policy
    lines = [
        f"Du bist {agent.name}, ein interner PI-Guardian-Agent.",
        f"Beschreibung: {agent.description}",
        f"Agent-Typ: {agent.agent_type}",
        f"Aktiv: {settings.active}",
        f"Read-only: {settings.read_only}",
        f"Bevorzugtes Modell: {settings.preferred_model or 'nicht gesetzt'}",
        f"Max Steps: {settings.max_steps}",
        f"Timeout Sekunden: {settings.timeout_seconds or 'nicht gesetzt'}",
        "Policy:",
        f"- Erlaubte Tools: {', '.join(policy.allowed_tools) if policy.allowed_tools else 'keine'}.",
        f"- Logs erlaubt: {policy.can_use_logs}",
        f"- Services erlaubt: {policy.can_use_services}",
        f"- Docker erlaubt: {policy.can_use_docker}",
        f"- Skills erlaubt: {policy.allowed_skills if policy.allowed_skills else 'keine'}",
        f"- Actions erlaubt: {policy.allowed_actions if policy.allowed_actions else 'keine'}",
        f"- Actions vorschlagen erlaubt: {policy.can_propose_actions}",
        f"- Maximale Tool-Aufrufe: {policy.max_tool_calls or 'nicht gesetzt'}",
        "Verhalten:",
        f"- Analysemodus: {settings.behavior.analysis_mode}",
        f"- Antworttiefe: {settings.behavior.response_depth}",
        f"- Priorisierung: {settings.behavior.prioritization_style}",
        f"- Unsicherheitsverhalten: {settings.behavior.uncertainty_behavior}",
        f"- Risikoempfindlichkeit: {settings.behavior.risk_sensitivity}",
        "Persönlichkeit:",
        f"- Stil: {settings.personality.style}",
        f"- Ton: {settings.personality.tone}",
        f"- Direktheit: {settings.personality.directness}",
        f"- Ausführlichkeit: {settings.personality.verbosity}",
        f"- Technische Strenge: {settings.personality.technical_strictness}",
        "Regeln:",
        "- Arbeite ausschließlich lesend.",
        f"- Erlaubte Tools: {', '.join(agent.allowed_tools) if agent.allowed_tools else 'keine'}.",
        "- Keine Shell, keine Schreibvorgänge, keine Neustarts, keine Änderungen.",
        "- Wenn ein Tool nötig ist, antworte ausschließlich mit einem JSON-Objekt im Format "
        '{"tool_name":"...","arguments":{...},"reason":"..."}.',
        "- Wenn ein Skill nötig ist, antworte ausschließlich mit einem JSON-Objekt im Format "
        '{"skill_name":"...","arguments":{...},"reason":"..."}.',
        "- Wenn eine Action vorgeschlagen werden soll, antworte ausschließlich mit einem JSON-Objekt im Format "
        '{"action_name":"...","arguments":{...},"reason":"...","target":"...","requires_approval":true}.',
        "- Wenn genügend Informationen vorliegen, antworte in Klartext ohne JSON.",
        "- Priorisiere Auffälligkeiten, nenne Risiken klar und empfehle nur Maßnahmen.",
    ]
    if settings.custom_instruction:
        lines.extend(["Benutzerhinweis:", settings.custom_instruction])
    return "\n".join(lines)


def build_prompt(
    agent: AgentDefinition,
    user_prompt: str,
    state: AgentRunState,
) -> str:
    return (
        f"=== SYSTEM ===\n{agent.system_prompt}\n\n"
        f"=== TOOL CATALOG ===\n{_render_tool_catalog(agent)}\n\n"
        f"=== SKILL CATALOG ===\n{_render_skill_catalog(agent)}\n\n"
        f"=== ACTION CATALOG ===\n{_render_action_catalog(agent)}\n\n"
        f"=== STEP STATE ===\n"
        f"- Aktueller Schritt: {state.current_step}/{state.max_steps}\n"
        f"- Tool-Aufrufe bisher: {state.tool_call_count}\n"
        f"- Skill-Aufrufe bisher: {state.skill_call_count}\n"
        f"- Abgeschlossen: {state.completed}\n\n"
        f"=== HISTORY ===\n{_render_history(state)}\n\n"
        f"=== USER REQUEST ===\n{user_prompt}\n\n"
        "=== OUTPUT RULES ===\n"
        "- Wenn du ein Tool aufrufen willst, antworte nur mit dem JSON-Objekt.\n"
        "- Wenn du fertig bist, antworte in normalem Klartext ohne JSON.\n"
        "- Keine weiteren Metadaten, keine Codeblöcke, keine Prosa vor oder nach dem JSON.\n"
    )
