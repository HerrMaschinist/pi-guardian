from __future__ import annotations

import asyncio
import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock

from guardian.app.core.domain import GuardianSeverity
from guardian.app.storage.models import (
    GuardianPersistenceReceipt,
    GuardianSnapshotHistory,
    GuardianSnapshotInput,
    GuardianSnapshotRecord,
    GuardianStateTransitionRecord,
)


@dataclass(frozen=True, slots=True)
class GuardianStorageConfig:
    path: str

    @classmethod
    def from_env(cls) -> "GuardianStorageConfig":
        path = os.getenv("GUARDIAN_STORAGE_PATH", "guardian/data/guardian.sqlite3").strip()
        if not path:
            path = "guardian/data/guardian.sqlite3"
        return cls(path=path)


class GuardianSQLiteStore:
    """Small SQLite store for Guardian snapshots and status transitions."""

    def __init__(self, config: GuardianStorageConfig) -> None:
        self._config = config
        self._lock = Lock()
        self._path = Path(config.path)
        self._init_error: str | None = None
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._ensure_schema()
        except Exception as exc:  # pragma: no cover - startup fallback
            self._init_error = str(exc)

    @property
    def path(self) -> Path:
        return self._path

    async def record_cycle(self, snapshot: GuardianSnapshotInput) -> GuardianPersistenceReceipt:
        return await asyncio.to_thread(self._record_cycle_sync, snapshot)

    async def get_last_snapshot(self) -> GuardianSnapshotRecord | None:
        return await asyncio.to_thread(self._get_last_snapshot_sync)

    async def get_last_status(self) -> GuardianSeverity | None:
        snapshot = await self.get_last_snapshot()
        return snapshot.guardian_status if snapshot is not None else None

    async def list_transitions(self, limit: int = 20) -> list[GuardianStateTransitionRecord]:
        return await asyncio.to_thread(self._list_transitions_sync, limit)

    async def list_snapshots(self, limit: int = 20) -> GuardianSnapshotHistory:
        return await asyncio.to_thread(self._list_snapshots_sync, limit)

    def _connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _ensure_schema(self) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS status_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    checked_at TEXT NOT NULL,
                    guardian_status TEXT NOT NULL,
                    router_status TEXT NOT NULL,
                    system_status TEXT NOT NULL,
                    overview_summary TEXT NOT NULL,
                    router_summary TEXT NOT NULL,
                    system_summary TEXT NOT NULL,
                    overview_reason_codes_json TEXT NOT NULL,
                    router_reason_codes_json TEXT NOT NULL,
                    system_reason_codes_json TEXT NOT NULL,
                    router_access_state TEXT NOT NULL,
                    router_readiness_state TEXT NOT NULL,
                    router_reachable INTEGER NOT NULL,
                    router_auth_required INTEGER NOT NULL,
                    system_running_as_root INTEGER NOT NULL,
                    system_cpu_usage_percent REAL,
                    system_memory_usage_percent REAL,
                    system_disk_usage_percent REAL,
                    system_temperature_c REAL,
                    evidence_json TEXT NOT NULL,
                    stored_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS state_transitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    previous_snapshot_id INTEGER,
                    current_snapshot_id INTEGER NOT NULL,
                    from_status TEXT NOT NULL,
                    to_status TEXT NOT NULL,
                    reason_codes_json TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    FOREIGN KEY(previous_snapshot_id) REFERENCES status_snapshots(id),
                    FOREIGN KEY(current_snapshot_id) REFERENCES status_snapshots(id)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_status_snapshots_checked_at ON status_snapshots(checked_at DESC)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_state_transitions_created_at ON state_transitions(created_at DESC)"
            )

    def _record_cycle_sync(self, snapshot: GuardianSnapshotInput) -> GuardianPersistenceReceipt:
        if self._init_error is not None:
            return GuardianPersistenceReceipt(
                ok=False,
                database_path=str(self._path),
                error=self._init_error,
            )

        try:
            with self._lock, self._connection() as conn:
                previous = self._load_last_snapshot_row(conn)
                snapshot_id = self._insert_snapshot(conn, snapshot)
                transition_id = None
                changed = False
                previous_status = previous["guardian_status"] if previous is not None else None
                current_status = snapshot.guardian_status

                if previous is not None and previous_status != current_status.value:
                    changed = True
                    transition_id = self._insert_transition(
                        conn,
                        previous_snapshot_id=int(previous["id"]),
                        current_snapshot_id=snapshot_id,
                        from_status=GuardianSeverity(previous_status),
                        to_status=current_status,
                        reason_codes=list(snapshot.overview_reason_codes),
                        summary=f"{previous_status} -> {current_status.value}",
                        evidence={
                            "previous_summary": previous["overview_summary"],
                            "current_summary": snapshot.overview_summary,
                            "previous_checked_at": previous["checked_at"],
                            "current_checked_at": snapshot.checked_at.isoformat(),
                        },
                    )

                return GuardianPersistenceReceipt(
                    ok=True,
                    database_path=str(self._path),
                    snapshot_id=snapshot_id,
                    transition_id=transition_id,
                    changed=changed,
                    previous_status=GuardianSeverity(previous_status) if previous_status is not None else None,
                    current_status=current_status,
                )
        except Exception as exc:  # pragma: no cover - defensive fallback
            return GuardianPersistenceReceipt(
                ok=False,
                database_path=str(self._path),
                error=str(exc),
                current_status=snapshot.guardian_status,
            )

    def _insert_snapshot(self, conn: sqlite3.Connection, snapshot: GuardianSnapshotInput) -> int:
        stored_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        cursor = conn.execute(
            """
            INSERT INTO status_snapshots (
                checked_at,
                guardian_status,
                router_status,
                system_status,
                overview_summary,
                router_summary,
                system_summary,
                overview_reason_codes_json,
                router_reason_codes_json,
                system_reason_codes_json,
                router_access_state,
                router_readiness_state,
                router_reachable,
                router_auth_required,
                system_running_as_root,
                system_cpu_usage_percent,
                system_memory_usage_percent,
                system_disk_usage_percent,
                system_temperature_c,
                evidence_json,
                stored_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot.checked_at.isoformat().replace("+00:00", "Z"),
                snapshot.guardian_status.value,
                snapshot.router_status.value,
                snapshot.system_status.value,
                snapshot.overview_summary,
                snapshot.router_summary,
                snapshot.system_summary,
                self._json(snapshot.overview_reason_codes),
                self._json(snapshot.router_reason_codes),
                self._json(snapshot.system_reason_codes),
                snapshot.router_access_state,
                snapshot.router_readiness_state,
                int(snapshot.router_reachable),
                int(snapshot.router_auth_required),
                int(snapshot.system_running_as_root),
                snapshot.system_cpu_usage_percent,
                snapshot.system_memory_usage_percent,
                snapshot.system_disk_usage_percent,
                snapshot.system_temperature_c,
                self._json(snapshot.evidence),
                stored_at,
            ),
        )
        return int(cursor.lastrowid)

    def _insert_transition(
        self,
        conn: sqlite3.Connection,
        *,
        previous_snapshot_id: int,
        current_snapshot_id: int,
        from_status: GuardianSeverity,
        to_status: GuardianSeverity,
        reason_codes: list[str],
        summary: str,
        evidence: dict[str, object],
    ) -> int:
        created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        cursor = conn.execute(
            """
            INSERT INTO state_transitions (
                created_at,
                previous_snapshot_id,
                current_snapshot_id,
                from_status,
                to_status,
                reason_codes_json,
                summary,
                evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                previous_snapshot_id,
                current_snapshot_id,
                from_status.value,
                to_status.value,
                self._json(reason_codes),
                summary,
                self._json(evidence),
            ),
        )
        return int(cursor.lastrowid)

    def _get_last_snapshot_sync(self) -> GuardianSnapshotRecord | None:
        if self._init_error is not None:
            return None
        with self._lock, self._connection() as conn:
            row = self._load_last_snapshot_row(conn)
            if row is None:
                return None
            return self._row_to_snapshot_record(row)

    def _list_transitions_sync(self, limit: int) -> list[GuardianStateTransitionRecord]:
        if self._init_error is not None:
            return []
        safe_limit = max(int(limit), 1)
        with self._lock, self._connection() as conn:
            rows = conn.execute(
                """
                SELECT id, created_at, previous_snapshot_id, current_snapshot_id, from_status, to_status,
                       reason_codes_json, summary, evidence_json
                FROM state_transitions
                ORDER BY id DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return [self._row_to_transition_record(row) for row in rows]

    def _list_snapshots_sync(self, limit: int) -> GuardianSnapshotHistory:
        if self._init_error is not None:
            return GuardianSnapshotHistory()
        safe_limit = max(int(limit), 1)
        with self._lock, self._connection() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM status_snapshots
                ORDER BY id DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return GuardianSnapshotHistory(items=[self._row_to_snapshot_record(row) for row in rows])

    def _load_last_snapshot_row(self, conn: sqlite3.Connection) -> sqlite3.Row | None:
        row = conn.execute(
            """
            SELECT *
            FROM status_snapshots
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
        return row

    def _row_to_snapshot_record(self, row: sqlite3.Row) -> GuardianSnapshotRecord:
        return GuardianSnapshotRecord(
            id=int(row["id"]),
            checked_at=self._parse_datetime(row["checked_at"]),
            guardian_status=GuardianSeverity(row["guardian_status"]),
            router_status=GuardianSeverity(row["router_status"]),
            system_status=GuardianSeverity(row["system_status"]),
            overview_summary=row["overview_summary"],
            router_summary=row["router_summary"],
            system_summary=row["system_summary"],
            overview_reason_codes=self._json_loads(row["overview_reason_codes_json"]),
            router_reason_codes=self._json_loads(row["router_reason_codes_json"]),
            system_reason_codes=self._json_loads(row["system_reason_codes_json"]),
            router_access_state=row["router_access_state"],
            router_readiness_state=row["router_readiness_state"],
            router_reachable=bool(row["router_reachable"]),
            router_auth_required=bool(row["router_auth_required"]),
            system_running_as_root=bool(row["system_running_as_root"]),
            system_cpu_usage_percent=row["system_cpu_usage_percent"],
            system_memory_usage_percent=row["system_memory_usage_percent"],
            system_disk_usage_percent=row["system_disk_usage_percent"],
            system_temperature_c=row["system_temperature_c"],
            evidence=self._json_loads(row["evidence_json"]),
            stored_at=self._parse_datetime(row["stored_at"]),
        )

    def _row_to_transition_record(self, row: sqlite3.Row) -> GuardianStateTransitionRecord:
        return GuardianStateTransitionRecord(
            id=int(row["id"]),
            created_at=self._parse_datetime(row["created_at"]),
            previous_snapshot_id=row["previous_snapshot_id"],
            current_snapshot_id=int(row["current_snapshot_id"]),
            from_status=GuardianSeverity(row["from_status"]),
            to_status=GuardianSeverity(row["to_status"]),
            reason_codes=self._json_loads(row["reason_codes_json"]),
            summary=row["summary"],
            evidence=self._json_loads(row["evidence_json"]),
        )

    def _json(self, value: object) -> str:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

    def _json_loads(self, raw: str | None) -> object:
        if raw is None or raw == "":
            return {}
        return json.loads(raw)

    def _parse_datetime(self, raw: str) -> datetime:
        value = raw.replace("Z", "+00:00")
        return datetime.fromisoformat(value)
