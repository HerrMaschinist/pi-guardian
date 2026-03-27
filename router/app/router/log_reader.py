import logging
from pathlib import Path

logger = logging.getLogger(__name__)

LOG_FILE = Path("logs/router.log")

LEVEL_MAP: dict[str, str] = {
    "DEBUG": "info",
    "INFO": "info",
    "WARNING": "warn",
    "WARN": "warn",
    "ERROR": "error",
    "CRITICAL": "error",
}


def _parse_line(line: str) -> dict | None:
    # Format: "2026-03-27 10:42:42,593 INFO uvicorn.error – message"
    try:
        if " \u2013 " not in line:
            return None
        header, _, message = line.partition(" \u2013 ")
        parts = header.split(" ", 3)
        if len(parts) < 4:
            return None
        date_str, time_str, level_str, source = parts
        timestamp = f"{date_str}T{time_str.replace(',', '.')}"
        level = LEVEL_MAP.get(level_str.upper(), "info")
        return {
            "timestamp": timestamp,
            "level": level,
            "source": source.strip(),
            "message": message.strip(),
        }
    except Exception:
        return None


def read_logs(limit: int = 50) -> list[dict]:
    if not LOG_FILE.exists():
        return []
    try:
        text = LOG_FILE.read_text(encoding="utf-8", errors="replace")
        entries: list[dict] = []
        for line in reversed(text.splitlines()):
            if not line.strip():
                continue
            parsed = _parse_line(line)
            if parsed:
                entries.append(parsed)
            if len(entries) >= limit:
                break
        return entries
    except Exception as exc:
        logger.warning("log_reader failed: %s", exc)
        return []
