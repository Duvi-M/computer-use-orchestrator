from __future__ import annotations

import base64
import hashlib
import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

from computer_use_demo.api.config import get_settings


class PostgresConnection:
    def __init__(self, conn: Any):
        self._conn = conn

    def execute(self, sql: str, params: tuple[Any, ...] = ()):
        return self._conn.execute(_postgres_sql(sql), _adapt_postgres_params(params))

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()


def get_db_path() -> Path:
    return get_settings().computer_use_db_path


def get_database_backend() -> str:
    return get_settings().database_backend


def _postgres_sql(sql: str) -> str:
    return sql.replace("?", "%s")


def _adapt_postgres_params(params: tuple[Any, ...]) -> tuple[Any, ...]:
    adapted = []
    for value in params:
        if isinstance(value, bool):
            adapted.append(value)
        else:
            adapted.append(value)
    return tuple(adapted)


def get_conn() -> Any:
    settings = get_settings()
    if settings.database_backend == "postgresql":
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError(
                "PostgreSQL support requires psycopg. Run `pip install -r requirements.txt`."
            ) from exc
        return PostgresConnection(psycopg.connect(settings.database_url, row_factory=dict_row))

    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    if get_database_backend() == "postgresql":
        _init_postgres_identity()
        return

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        created_at REAL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS organizations (
        id TEXT PRIMARY KEY,
        created_at REAL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS organization_memberships (
        user_id TEXT NOT NULL,
        organization_id TEXT NOT NULL,
        role TEXT DEFAULT 'member',
        created_at REAL,
        PRIMARY KEY (user_id, organization_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        organization_id TEXT,
        created_at REAL,
        last_activity REAL,
        status TEXT DEFAULT 'created',
        error TEXT,
        stop_reason TEXT,
        completed_at REAL,
        deleted_at REAL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        role TEXT,
        text TEXT,
        ts REAL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        event TEXT,
        data TEXT,
        ts REAL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS artifacts (
        artifact_id TEXT PRIMARY KEY,
        session_id TEXT,
        user_id TEXT,
        organization_id TEXT,
        event_id INTEGER,
        message_id INTEGER,
        artifact_type TEXT,
        media_type TEXT,
        storage_path TEXT,
        size_bytes INTEGER,
        checksum TEXT,
        created_at REAL,
        expires_at REAL,
        deleted_at REAL
    )
    """)

    conn.commit()
    _ensure_session_columns(conn)
    _ensure_artifact_table(conn)
    settings = get_settings()
    ensure_identity(settings.dev_user_id, settings.dev_org_id, conn=conn)
    _backfill_session_owners(conn, settings.dev_user_id, settings.dev_org_id)
    conn.close()


def _init_postgres_identity() -> None:
    settings = get_settings()
    try:
        conn = get_conn()
    except Exception as exc:
        raise RuntimeError(
            "PostgreSQL database is not reachable; verify DATABASE_URL and run "
            "`alembic upgrade head` before starting the API."
        ) from exc
    try:
        ensure_identity(settings.dev_user_id, settings.dev_org_id, conn=conn)
    except Exception as exc:
        raise RuntimeError(
            "PostgreSQL schema is not initialized; run `alembic upgrade head`."
        ) from exc
    finally:
        conn.close()


def _ensure_session_columns(conn: sqlite3.Connection) -> None:
    existing = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(sessions)")
    }
    columns = {
        "user_id": "TEXT",
        "organization_id": "TEXT",
        "status": "TEXT DEFAULT 'created'",
        "error": "TEXT",
        "stop_reason": "TEXT",
        "completed_at": "REAL",
        "deleted_at": "REAL",
    }
    for name, definition in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE sessions ADD COLUMN {name} {definition}")
    conn.commit()


def _ensure_artifact_table(conn: sqlite3.Connection) -> None:
    existing = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(artifacts)")
    }
    columns = {
        "artifact_id": "TEXT PRIMARY KEY",
        "session_id": "TEXT",
        "user_id": "TEXT",
        "organization_id": "TEXT",
        "event_id": "INTEGER",
        "message_id": "INTEGER",
        "artifact_type": "TEXT",
        "media_type": "TEXT",
        "storage_path": "TEXT",
        "size_bytes": "INTEGER",
        "checksum": "TEXT",
        "created_at": "REAL",
        "expires_at": "REAL",
        "deleted_at": "REAL",
    }
    for name, definition in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE artifacts ADD COLUMN {name} {definition}")
    conn.commit()


def _backfill_session_owners(
    conn: sqlite3.Connection,
    default_user_id: str,
    default_org_id: str,
) -> None:
    conn.execute(
        "UPDATE sessions SET user_id = ? WHERE user_id IS NULL OR user_id = ''",
        (default_user_id,),
    )
    conn.execute(
        """
        UPDATE sessions
        SET organization_id = ?
        WHERE organization_id IS NULL OR organization_id = ''
        """,
        (default_org_id,),
    )
    conn.commit()


def ensure_identity(
    user_id: str,
    organization_id: str,
    *,
    conn: sqlite3.Connection | None = None,
) -> None:
    owns_conn = conn is None
    if conn is None:
        conn = get_conn()
    now = time.time()
    if get_database_backend() == "postgresql":
        conn.execute(
            """
            INSERT INTO users (id, created_at)
            VALUES (?, ?)
            ON CONFLICT (id) DO NOTHING
            """,
            (user_id, now),
        )
        conn.execute(
            """
            INSERT INTO organizations (id, created_at)
            VALUES (?, ?)
            ON CONFLICT (id) DO NOTHING
            """,
            (organization_id, now),
        )
        conn.execute(
            """
            INSERT INTO organization_memberships
                (user_id, organization_id, role, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (user_id, organization_id) DO NOTHING
            """,
            (user_id, organization_id, "member", now),
        )
    else:
        conn.execute(
            "INSERT OR IGNORE INTO users (id, created_at) VALUES (?, ?)",
            (user_id, now),
        )
        conn.execute(
            "INSERT OR IGNORE INTO organizations (id, created_at) VALUES (?, ?)",
            (organization_id, now),
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO organization_memberships
                (user_id, organization_id, role, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, organization_id, "member", now),
        )
    conn.commit()
    if owns_conn:
        conn.close()


def insert_session(
    session_id: str,
    user_id: str | None = None,
    organization_id: str | None = None,
) -> None:
    now = time.time()
    settings = get_settings()
    user_id = user_id or settings.dev_user_id
    organization_id = organization_id or settings.dev_org_id
    conn = get_conn()
    ensure_identity(user_id, organization_id, conn=conn)
    conn.execute(
        """
        INSERT INTO sessions
            (id, user_id, organization_id, created_at, last_activity, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (session_id, user_id, organization_id, now, now, "created"),
    )
    conn.commit()
    conn.close()


def get_session_owner(session_id: str) -> dict[str, Any] | None:
    conn = get_conn()
    row = conn.execute(
        """
        SELECT id, user_id, organization_id
        FROM sessions
        WHERE id = ? AND deleted_at IS NULL
        """,
        (session_id,),
    ).fetchone()
    conn.close()
    return None if row is None else dict(row)


def update_session_activity(session_id: str) -> None:
    conn = get_conn()
    conn.execute(
        "UPDATE sessions SET last_activity = ? WHERE id = ?",
        (time.time(), session_id),
    )
    conn.commit()
    conn.close()


def update_session_status(
    session_id: str,
    status: str,
    error: str | None = None,
    completed: bool = False,
    stop_reason: str | None = None,
    deleted: bool = False,
) -> None:
    conn = get_conn()
    conn.execute(
        """
        UPDATE sessions
        SET
            status = ?,
            error = ?,
            stop_reason = COALESCE(?, stop_reason),
            completed_at = CASE WHEN ? THEN ? ELSE completed_at END,
            deleted_at = CASE WHEN ? THEN ? ELSE deleted_at END
        WHERE id = ?
        """,
        (
            status,
            error,
            stop_reason,
            completed,
            time.time(),
            deleted,
            time.time(),
            session_id,
        ),
    )
    conn.commit()
    conn.close()


def insert_message(session_id: str, role: str, text: str) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT INTO messages (session_id, role, text, ts) VALUES (?, ?, ?, ?)",
        (session_id, role, text, time.time()),
    )
    conn.commit()
    conn.close()


def count_session_messages(session_id: str, role: str | None = None) -> int:
    conn = get_conn()
    if role is None:
        row = conn.execute(
            "SELECT COUNT(*) AS count FROM messages WHERE session_id = ?",
            (session_id,),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT COUNT(*) AS count FROM messages WHERE session_id = ? AND role = ?",
            (session_id, role),
        ).fetchone()
    conn.close()
    return int(row["count"])


def count_session_events(session_id: str) -> int:
    conn = get_conn()
    row = conn.execute(
        "SELECT COUNT(*) AS count FROM events WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    conn.close()
    return int(row["count"])


def get_session_record(session_id: str) -> dict[str, Any] | None:
    conn = get_conn()
    row = conn.execute(
        """
        SELECT id, user_id, organization_id, created_at, last_activity, status,
               error, stop_reason, completed_at, deleted_at
        FROM sessions
        WHERE id = ?
        """,
        (session_id,),
    ).fetchone()
    conn.close()
    return None if row is None else dict(row)


def get_session_history(session_id: str) -> dict[str, Any] | None:
    conn = get_conn()
    session = conn.execute(
        """
        SELECT id, user_id, organization_id, created_at, last_activity, status,
               error, stop_reason, completed_at, deleted_at
        FROM sessions
        WHERE id = ?
        """,
        (session_id,),
    ).fetchone()

    if session is None:
        conn.close()
        return None

    messages = [
        dict(row)
        for row in conn.execute(
            """
            SELECT id, role, text, ts
            FROM messages
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        )
    ]
    events = []
    for row in conn.execute(
        """
        SELECT id, event, data, ts
        FROM events
        WHERE session_id = ?
        ORDER BY id ASC
        """,
        (session_id,),
    ):
        item = dict(row)
        if isinstance(item["data"], str):
            try:
                item["data"] = json.loads(item["data"])
            except (TypeError, json.JSONDecodeError):
                item["data"] = {"raw": item["data"]}
        events.append(item)

    conn.close()
    return {
        "session": dict(session),
        "messages": messages,
        "events": events,
    }


def insert_event(session_id: str, event: str, data: dict[str, Any]) -> int | None:
    conn = get_conn()
    payload: Any = json.dumps(data)
    if get_database_backend() == "postgresql":
        try:
            from psycopg.types.json import Jsonb
        except ImportError as exc:
            raise RuntimeError(
                "PostgreSQL support requires psycopg. Run `pip install -r requirements.txt`."
            ) from exc
        payload = Jsonb(data)
        row = conn.execute(
            """
            INSERT INTO events (session_id, event, data, ts)
            VALUES (?, ?, ?, ?)
            RETURNING id
            """,
            (session_id, event, payload, time.time()),
        ).fetchone()
        event_id = None if row is None else int(row["id"])
    else:
        cursor = conn.execute(
            "INSERT INTO events (session_id, event, data, ts) VALUES (?, ?, ?, ?)",
            (session_id, event, payload, time.time()),
        )
        event_id = int(cursor.lastrowid)
    conn.commit()
    conn.close()
    return event_id


def _retention_expiry(now: float, days: int) -> float:
    return now + (days * 86400)


def create_artifact_metadata(
    *,
    session_id: str,
    artifact_type: str,
    media_type: str,
    storage_path: str | None = None,
    size_bytes: int | None = None,
    checksum: str | None = None,
    event_id: int | None = None,
    message_id: int | None = None,
    expires_at: float | None = None,
    artifact_id: str | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    record = get_session_record(session_id)
    now = time.time()
    artifact_id = artifact_id or str(uuid.uuid4())
    user_id = None if record is None else record.get("user_id")
    organization_id = None if record is None else record.get("organization_id")
    if expires_at is None:
        expires_at = _retention_expiry(now, settings.screenshot_retention_days)

    conn = get_conn()
    conn.execute(
        """
        INSERT INTO artifacts
            (artifact_id, session_id, user_id, organization_id, event_id, message_id,
             artifact_type, media_type, storage_path, size_bytes, checksum, created_at,
             expires_at, deleted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            artifact_id,
            session_id,
            user_id,
            organization_id,
            event_id,
            message_id,
            artifact_type,
            media_type,
            storage_path,
            size_bytes,
            checksum,
            now,
            expires_at,
            None,
        ),
    )
    conn.commit()
    conn.close()
    return {
        "artifact_id": artifact_id,
        "session_id": session_id,
        "user_id": user_id,
        "organization_id": organization_id,
        "event_id": event_id,
        "message_id": message_id,
        "artifact_type": artifact_type,
        "media_type": media_type,
        "storage_path": storage_path,
        "size_bytes": size_bytes,
        "checksum": checksum,
        "created_at": now,
        "expires_at": expires_at,
        "deleted_at": None,
    }


def _decode_base64_image(raw: Any) -> bytes | None:
    if not isinstance(raw, str) or not raw:
        return None
    if "," in raw and raw.startswith("data:"):
        raw = raw.split(",", 1)[1]
    try:
        return base64.b64decode(raw, validate=False)
    except Exception:
        return None


def create_screenshot_artifact(
    session_id: str,
    event_id: int | None,
    data: dict[str, Any],
) -> dict[str, Any] | None:
    image = (
        data.get("image_base64")
        or data.get("screenshot_base64")
        or data.get("screenshot")
    )
    image_bytes = _decode_base64_image(image)
    artifact_id = str(uuid.uuid4())
    storage_path = None
    size_bytes = None
    checksum = None
    if image_bytes:
        settings = get_settings()
        artifact_dir = settings.artifact_storage_dir / session_id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = artifact_dir / f"{artifact_id}.png"
        artifact_path.write_bytes(image_bytes)
        storage_path = str(artifact_path)
        size_bytes = len(image_bytes)
        checksum = hashlib.sha256(image_bytes).hexdigest()

    return create_artifact_metadata(
        session_id=session_id,
        artifact_id=artifact_id,
        event_id=event_id,
        artifact_type="screenshot",
        media_type="image/png",
        storage_path=storage_path,
        size_bytes=size_bytes,
        checksum=checksum,
    )


def list_artifacts(
    *,
    session_id: str | None = None,
    include_deleted: bool = False,
) -> list[dict[str, Any]]:
    conn = get_conn()
    where = []
    params: list[Any] = []
    if session_id is not None:
        where.append("session_id = ?")
        params.append(session_id)
    if not include_deleted:
        where.append("deleted_at IS NULL")
    where_sql = "" if not where else "WHERE " + " AND ".join(where)
    rows = [
        dict(row)
        for row in conn.execute(
            f"""
            SELECT artifact_id, session_id, user_id, organization_id, event_id,
                   message_id, artifact_type, media_type, storage_path, size_bytes,
                   checksum, created_at, expires_at, deleted_at
            FROM artifacts
            {where_sql}
            ORDER BY created_at ASC
            """,
            tuple(params),
        )
    ]
    conn.close()
    return rows


def _count_where(table: str, where_sql: str, params: tuple[Any, ...]) -> int:
    conn = get_conn()
    try:
        row = conn.execute(
            f"SELECT COUNT(*) AS count FROM {table} WHERE {where_sql}",
            params,
        ).fetchone()
        if isinstance(row, dict):
            return int(row["count"])
        return int(row["count"])
    finally:
        conn.close()


def _delete_where(table: str, where_sql: str, params: tuple[Any, ...]) -> int:
    conn = get_conn()
    try:
        count = _count_where(table, where_sql, params)
        conn.execute(f"DELETE FROM {table} WHERE {where_sql}", params)
        conn.commit()
        return count
    finally:
        conn.close()


def _soft_delete_expired_artifacts(now: float, dry_run: bool) -> int:
    where_sql = "expires_at IS NOT NULL AND expires_at <= ? AND deleted_at IS NULL"
    count = _count_where("artifacts", where_sql, (now,))
    if dry_run or count == 0:
        return count
    conn = get_conn()
    try:
        rows = [
            dict(row)
            for row in conn.execute(
                "SELECT artifact_id, storage_path FROM artifacts WHERE " + where_sql,
                (now,),
            )
        ]
        for row in rows:
            storage_path = row.get("storage_path")
            if storage_path:
                Path(storage_path).unlink(missing_ok=True)
        conn.execute(
            "UPDATE artifacts SET deleted_at = ? WHERE " + where_sql,
            (now, now),
        )
        conn.commit()
        return count
    finally:
        conn.close()


def cleanup_retention(*, dry_run: bool = True, now: float | None = None) -> dict[str, Any]:
    settings = get_settings()
    now = time.time() if now is None else now
    message_cutoff = now - (settings.message_retention_days * 86400)
    event_cutoff = now - (settings.event_retention_days * 86400)
    deleted_session_cutoff = now - (settings.deleted_session_retention_days * 86400)
    worker_log_cutoff = now - (settings.worker_log_retention_days * 86400)

    report = {
        "dry_run": dry_run,
        "message_cutoff": message_cutoff,
        "event_cutoff": event_cutoff,
        "deleted_session_cutoff": deleted_session_cutoff,
        "worker_log_cutoff": worker_log_cutoff,
        "messages": _count_where("messages", "ts <= ?", (message_cutoff,)),
        "events": _count_where("events", "ts <= ?", (event_cutoff,)),
        "artifacts": _count_where(
            "artifacts",
            "expires_at IS NOT NULL AND expires_at <= ? AND deleted_at IS NULL",
            (now,),
        ),
        "deleted_sessions": _count_where(
            "sessions",
            "deleted_at IS NOT NULL AND deleted_at <= ?",
            (deleted_session_cutoff,),
        ),
    }
    if dry_run:
        return report

    report["messages"] = _delete_where("messages", "ts <= ?", (message_cutoff,))
    report["events"] = _delete_where("events", "ts <= ?", (event_cutoff,))
    report["artifacts"] = _soft_delete_expired_artifacts(now, dry_run=False)

    conn = get_conn()
    try:
        deleted_sessions = [
            dict(row)
            for row in conn.execute(
                """
                SELECT id
                FROM sessions
                WHERE deleted_at IS NOT NULL AND deleted_at <= ?
                """,
                (deleted_session_cutoff,),
            )
        ]
        for row in deleted_sessions:
            session_id = row["id"]
            artifact_rows = [
                dict(artifact)
                for artifact in conn.execute(
                    "SELECT storage_path FROM artifacts WHERE session_id = ?",
                    (session_id,),
                )
            ]
            for artifact in artifact_rows:
                storage_path = artifact.get("storage_path")
                if storage_path:
                    Path(storage_path).unlink(missing_ok=True)
            conn.execute("DELETE FROM artifacts WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM events WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
        report["deleted_sessions"] = len(deleted_sessions)
    finally:
        conn.close()
    return report
