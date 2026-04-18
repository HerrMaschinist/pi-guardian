from typing import Any, Literal

from pydantic import BaseModel, Field


class RoutePolicyTrace(BaseModel):
    can_use_llm: bool
    can_use_tools: bool
    can_use_internet: bool
    decision_classification: Literal[
        "llm_only", "tool_required", "internet_required", "blocked"
    ]
    tool_execution_allowed: bool
    internet_execution_allowed: bool


class RouteToolExecution(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    reason: str
    success: bool
    duration_ms: int
    output: Any = None
    error: str | None = None


class RouteResponse(BaseModel):
    request_id: str
    model: str
    response: str
    done: bool
    done_reason: str | None = None
    duration_ms: int
    decision_classification: Literal[
        "llm_only", "tool_required", "internet_required", "blocked"
    ] = "llm_only"
    decision_reasons: list[str] = Field(default_factory=list)
    decision_tool_hints: list[str] = Field(default_factory=list)
    decision_internet_hints: list[str] = Field(default_factory=list)
    fairness_review_attempted: bool = False
    fairness_review_used: bool = False
    fairness_risk: str = "unknown"
    fairness_review_override: bool = False
    fairness_reasons: list[str] = Field(default_factory=list)
    fairness_notes: list[str] = Field(default_factory=list)
    execution_mode: Literal["llm", "tool", "internet_pending"] = "llm"
    policy_trace: RoutePolicyTrace | None = None
    tool_executions: list[RouteToolExecution] = Field(default_factory=list)
    execution_error: str | None = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    retryable: bool = False


class RouteErrorResponse(BaseModel):
    request_id: str
    model: str | None = None
    error: ErrorDetail


class SettingsUpdateResponse(BaseModel):
    settings: "RouterSettings"
    restart_requested: bool
    restart_performed: bool
    restart_message: str | None = None
    validation_warnings: list[str] = Field(default_factory=list)


class ServiceStatus(BaseModel):
    service: str
    active: bool
    uptime: str | None = None
    pid: int | None = None
    memory_usage: str | None = None
    cpu_percent: float | None = None


class LogEntry(BaseModel):
    timestamp: str
    level: Literal["info", "warn", "error"]
    source: str
    message: str


class OllamaModel(BaseModel):
    name: str
    size: str
    modified_at: str
    digest: str


class RouterSettings(BaseModel):
    router_host: str
    router_port: int
    ollama_host: str
    ollama_port: int
    timeout: int
    default_model: str
    large_model: str
    logging_level: str
    stream_default: bool
    require_api_key: bool
    escalation_threshold: str


class IntegrationGuide(BaseModel):
    router_base_url: str
    auth_header_name: str
    auth_header_example: str
    allowed_routes: list[str]
    security_controls: list[str]
    example_create_client: dict[str, Any]
    example_curl: str


class RouteHistoryEntry(BaseModel):
    id: int
    request_id: str
    prompt_preview: str
    model: str | None = None
    success: bool
    error_code: str | None = None
    client_name: str | None = None
    duration_ms: int | None = None
    decision_classification: Literal[
        "llm_only", "tool_required", "internet_required", "blocked"
    ] = "llm_only"
    decision_reasons: list[str] = Field(default_factory=list)
    decision_tool_hints: list[str] = Field(default_factory=list)
    decision_internet_hints: list[str] = Field(default_factory=list)
    fairness_review_attempted: bool = False
    fairness_review_used: bool = False
    fairness_risk: str = "unknown"
    fairness_review_override: bool = False
    escalation_threshold: str | None = None
    fairness_reasons: list[str] = Field(default_factory=list)
    fairness_notes: list[str] = Field(default_factory=list)
    policy_trace: dict[str, Any] = Field(default_factory=dict)
    execution_mode: Literal["llm", "tool", "internet_pending"] = "llm"
    execution_status: Literal["not_executed", "succeeded", "failed"] = "not_executed"
    executed_tools: list[str] = Field(default_factory=list)
    tool_execution_records: list[dict[str, Any]] = Field(default_factory=list)
    execution_error: str | None = None
    created_at: str
