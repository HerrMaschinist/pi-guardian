from __future__ import annotations

import os
import shutil
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from app.models.agent_models import ToolResult
from app.tools.base import BaseTool


class SystemStatusInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _read_meminfo() -> dict[str, float | int]:
    info: dict[str, int] = {}
    with Path("/proc/meminfo").open("r", encoding="utf-8") as handle:
        for line in handle:
            if ":" not in line:
                continue
            key, _, rest = line.partition(":")
            parts = rest.strip().split()
            if not parts:
                continue
            try:
                info[key] = int(parts[0])
            except ValueError:
                continue

    total_kb = info.get("MemTotal", 0)
    available_kb = info.get("MemAvailable", 0)
    used_kb = max(total_kb - available_kb, 0)
    used_percent = (used_kb / total_kb * 100) if total_kb else None
    return {
        "total_mb": round(total_kb / 1024, 1),
        "available_mb": round(available_kb / 1024, 1),
        "used_mb": round(used_kb / 1024, 1),
        "used_percent": round(used_percent, 1) if used_percent is not None else None,
    }


def _read_uptime_seconds() -> float | None:
    try:
        raw = Path("/proc/uptime").read_text(encoding="utf-8").split()[0]
        return float(raw)
    except Exception:
        return None


def _read_temperature_c() -> float | None:
    candidates = [
        Path("/sys/class/thermal/thermal_zone0/temp"),
        Path("/sys/class/hwmon/hwmon0/temp1_input"),
    ]
    for candidate in candidates:
        try:
            raw = candidate.read_text(encoding="utf-8").strip()
            value = float(raw)
            if value > 1000:
                return round(value / 1000.0, 1)
            return round(value, 1)
        except Exception:
            continue
    return None


def _read_load_average() -> dict[str, float] | None:
    try:
        load1, load5, load15 = os.getloadavg()
    except (OSError, AttributeError):
        return None
    return {
        "1m": round(load1, 2),
        "5m": round(load5, 2),
        "15m": round(load15, 2),
    }


class SystemStatusTool(BaseTool):
    name = "system_status"
    description = "Liest Uptime, CPU-, Speicher-, Disk- und Temperaturdaten des Systems."
    input_schema = SystemStatusInput
    read_only = True
    category = "system"

    def execute(self, validated_input: BaseModel) -> ToolResult:
        del validated_input
        try:
            disk_usage = shutil.disk_usage("/")
            used_percent = (disk_usage.used / disk_usage.total * 100) if disk_usage.total else 0.0
            output = {
                "uptime_seconds": _read_uptime_seconds(),
                "load_average": _read_load_average(),
                "memory": _read_meminfo(),
                "disk": {
                    "mount": "/",
                    "total_gb": round(disk_usage.total / (1024 ** 3), 2),
                    "used_gb": round(disk_usage.used / (1024 ** 3), 2),
                    "free_gb": round(disk_usage.free / (1024 ** 3), 2),
                    "used_percent": round(used_percent, 1),
                },
                "temperature_c": _read_temperature_c(),
            }
            return ToolResult(tool_name=self.name, success=True, output=output)
        except Exception as exc:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Systemstatus konnte nicht gelesen werden: {exc}",
            )
