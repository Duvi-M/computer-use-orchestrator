from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_QUEUE_DB = Path("data") / "task_queue.db"
QUEUE_LOCK_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True)
class ClaimedTask:
    id: int
    status: str
    assigned_agent: str
    payload: dict[str, Any]
    updated_at: str


def utc_timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def connect(db_path: Path = DEFAULT_QUEUE_DB) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(
        db_path,
        timeout=QUEUE_LOCK_TIMEOUT_SECONDS,
        isolation_level=None,
    )
    conn.row_factory = sqlite3.Row
    return conn


def init_queue(db_path: Path = DEFAULT_QUEUE_DB) -> None:
    with connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT NOT NULL DEFAULT 'pending',
                assigned_agent TEXT,
                payload TEXT NOT NULL,
                result TEXT,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status_id ON tasks(status, id)")


def enqueue_task(payload: dict[str, Any], db_path: Path = DEFAULT_QUEUE_DB) -> int:
    init_queue(db_path)
    with connect(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO tasks (status, assigned_agent, payload, updated_at)
            VALUES ('pending', NULL, ?, ?)
            """,
            (json.dumps(payload, sort_keys=True), utc_timestamp()),
        )
        return int(cursor.lastrowid)


def claim_next_task(
    agent_id: str,
    db_path: Path = DEFAULT_QUEUE_DB,
) -> ClaimedTask | None:
    init_queue(db_path)
    with connect(db_path) as conn:
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                """
                SELECT id, status, assigned_agent, payload, updated_at
                FROM tasks
                WHERE status = 'pending'
                ORDER BY id
                LIMIT 1
                """
            ).fetchone()
            if row is None:
                conn.execute("COMMIT")
                return None

            updated_at = utc_timestamp()
            conn.execute(
                """
                UPDATE tasks
                SET status = 'claimed',
                    assigned_agent = ?,
                    updated_at = ?
                WHERE id = ? AND status = 'pending'
                """,
                (agent_id, updated_at, row["id"]),
            )
            conn.execute("COMMIT")
            return ClaimedTask(
                id=int(row["id"]),
                status="claimed",
                assigned_agent=agent_id,
                payload=json.loads(row["payload"]),
                updated_at=updated_at,
            )
        except sqlite3.OperationalError as exc:
            if "database is locked" in str(exc).lower():
                raise RuntimeError(
                    "task queue busy (database locked) after "
                    f"{QUEUE_LOCK_TIMEOUT_SECONDS:g}s, agent_id={agent_id} "
                    "- check for a stale lock or another process holding a "
                    "long transaction."
                ) from exc
            conn.execute("ROLLBACK")
            raise
        except Exception:
            conn.execute("ROLLBACK")
            raise


def complete_task(
    task_id: int,
    result: dict[str, Any] | str,
    db_path: Path = DEFAULT_QUEUE_DB,
) -> None:
    init_queue(db_path)
    result_payload = result if isinstance(result, str) else json.dumps(result, sort_keys=True)
    with connect(db_path) as conn:
        conn.execute(
            """
            UPDATE tasks
            SET status = 'completed',
                result = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (result_payload, utc_timestamp(), task_id),
        )


def list_tasks(db_path: Path = DEFAULT_QUEUE_DB) -> list[dict[str, Any]]:
    init_queue(db_path)
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, status, assigned_agent, payload, result, updated_at
            FROM tasks
            ORDER BY id
            """
        ).fetchall()
    return [
        {
            "id": int(row["id"]),
            "status": row["status"],
            "assigned_agent": row["assigned_agent"],
            "payload": json.loads(row["payload"]),
            "result": row["result"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]
