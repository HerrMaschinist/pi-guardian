from pydantic import BaseModel, Field


class RouteRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Eingabetext für das Modell")
    preferred_model: str | None = Field(
        default=None,
        description="Optional gewünschtes Modell, z. B. qwen2.5-coder:1.5b",
    )
    stream: bool = Field(
        default=False,
        description="Streaming für Phase 1 deaktiviert, Feld bleibt für Kompatibilität erhalten",
    )


class ModelSelectionRequest(BaseModel):
    model: str = Field(..., min_length=1, description="Neues Standardmodell")
