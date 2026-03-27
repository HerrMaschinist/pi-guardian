import logging
import subprocess
from datetime import datetime

logger = logging.getLogger(__name__)

SERVICE_NAME = "pi-guardian-router"


def _run(cmd: list[str]) -> str | None:
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception as exc:
        logger.warning("system_status subprocess failed: %s", exc)
        return None


def get_service_status() -> dict:
    base: dict = {
        "service": SERVICE_NAME,
        "active": False,
        "uptime": None,
        "pid": None,
        "memory_usage": None,
        "cpu_percent": None,
    }

    # 1. is-active
    active_out = _run(["systemctl", "is-active", SERVICE_NAME])
    if active_out is None:
        return base  # systemctl not available
    base["active"] = active_out == "active"

    # 2. show properties
    show_out = _run([
        "systemctl", "show", SERVICE_NAME,
        "--property=MainPID,ActiveEnterTimestamp,MemoryCurrent",
    ])
    if not show_out:
        return base

    props: dict[str, str] = {}
    for line in show_out.splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            props[k.strip()] = v.strip()

    # PID
    pid_str = props.get("MainPID", "0")
    try:
        pid = int(pid_str)
        base["pid"] = pid if pid > 0 else None
    except ValueError:
        pass

    # Memory
    mem_str = props.get("MemoryCurrent", "")
    try:
        mem_bytes = int(mem_str)
        base["memory_usage"] = f"{mem_bytes / (1024 ** 2):.1f} MB"
    except ValueError:
        pass

    # Uptime from ActiveEnterTimestamp
    ts_str = props.get("ActiveEnterTimestamp", "")
    if ts_str:
        try:
            # Format: "Thu 2026-03-23 21:18:16 CET"
            # Strip weekday prefix and timezone suffix, parse what remains
            parts = ts_str.split()
            if len(parts) >= 3:
                dt_str = f"{parts[1]} {parts[2]}"
                start = datetime.fromisoformat(dt_str)
                delta = datetime.now() - start
                total = int(delta.total_seconds())
                days = total // 86400
                hours = (total % 86400) // 3600
                minutes = (total % 3600) // 60
                seconds = total % 60
                base["uptime"] = f"{days} days, {hours}:{minutes:02d}:{seconds:02d}"
        except Exception as exc:
            logger.debug("uptime parse failed: %s", exc)

    # 3. CPU via ps (optional, best-effort)
    if base["pid"]:
        cpu_out = _run(["ps", "-p", str(base["pid"]), "-o", "%cpu="])
        if cpu_out:
            try:
                base["cpu_percent"] = float(cpu_out.strip())
            except ValueError:
                pass

    return base
