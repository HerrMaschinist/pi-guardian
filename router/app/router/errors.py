from dataclasses import dataclass


@dataclass
class RouterApiError(Exception):
    message: str
    status_code: int
    code: str
    request_id: str
    model: str | None = None
    retryable: bool = False

    def __str__(self) -> str:
        return self.message
