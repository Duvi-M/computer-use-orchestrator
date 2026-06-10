import sqlite3
import time
import base64

from computer_use_demo.api import db


def test_init_db_uses_configurable_path(tmp_path, monkeypatch):
    db_path = tmp_path / "nested" / "orchestrator.db"
    monkeypatch.setenv("COMPUTER_USE_DB_PATH", str(db_path))

    db.init_db()

    assert db_path.exists()

    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert {
        "users",
        "organizations",
        "organization_memberships",
        "sessions",
        "messages",
        "events",
        "artifacts",
    }.issubset(tables)
    assert {"status", "error", "stop_reason", "completed_at", "deleted_at"}.issubset(
        {
            row[1]
            for row in conn.execute("PRAGMA table_info(sessions)")
        }
    )
    assert {"artifact_id", "session_id", "artifact_type", "expires_at", "deleted_at"}.issubset(
        {
            row[1]
            for row in conn.execute("PRAGMA table_info(artifacts)")
        }
    )
    assert {"user_id", "organization_id"}.issubset(
        {
            row[1]
            for row in conn.execute("PRAGMA table_info(sessions)")
        }
    )


def test_session_history_persists_messages_events_and_status(tmp_path, monkeypatch):
    db_path = tmp_path / "orchestrator.db"
    monkeypatch.setenv("COMPUTER_USE_DB_PATH", str(db_path))

    db.init_db()
    db.insert_session("session-1")
    db.update_session_status("session-1", "running")
    db.insert_message("session-1", "user", "hello")
    db.insert_message("session-1", "assistant", "hi")
    db.insert_event("session-1", "done", {"ok": True})
    db.update_session_status("session-1", "completed", completed=True)

    history = db.get_session_history("session-1")

    assert history is not None
    assert history["session"]["status"] == "completed"
    assert history["session"]["user_id"] == "dev-user"
    assert history["session"]["organization_id"] == "dev-org"
    assert [message["role"] for message in history["messages"]] == ["user", "assistant"]
    assert history["events"][0]["event"] == "done"
    assert history["events"][0]["data"] == {"ok": True}


def test_insert_session_stores_owner(tmp_path, monkeypatch):
    db_path = tmp_path / "owners.db"
    monkeypatch.setenv("COMPUTER_USE_DB_PATH", str(db_path))

    db.init_db()
    db.insert_session("session-owned", user_id="user-a", organization_id="org-a")

    owner = db.get_session_owner("session-owned")
    history = db.get_session_history("session-owned")

    assert owner == {
        "id": "session-owned",
        "user_id": "user-a",
        "organization_id": "org-a",
    }
    assert history is not None
    assert history["session"]["user_id"] == "user-a"
    assert history["session"]["organization_id"] == "org-a"


def test_soft_deleted_session_owner_is_hidden_but_history_remains(tmp_path, monkeypatch):
    db_path = tmp_path / "soft-delete.db"
    monkeypatch.setenv("COMPUTER_USE_DB_PATH", str(db_path))

    db.init_db()
    db.insert_session("session-deleted", user_id="user-a", organization_id="org-a")
    db.insert_message("session-deleted", "user", "keep for retention")
    db.update_session_status("session-deleted", "deleted", completed=True, deleted=True)

    assert db.get_session_owner("session-deleted") is None
    history = db.get_session_history("session-deleted")
    assert history is not None
    assert history["session"]["deleted_at"] is not None
    assert history["messages"][0]["text"] == "keep for retention"


def test_artifact_metadata_insert_and_read(tmp_path, monkeypatch):
    db_path = tmp_path / "artifacts.db"
    artifact_dir = tmp_path / "artifacts"
    monkeypatch.setenv("COMPUTER_USE_DB_PATH", str(db_path))
    monkeypatch.setenv("ARTIFACT_STORAGE_DIR", str(artifact_dir))

    db.init_db()
    db.insert_session("session-artifact", user_id="user-a", organization_id="org-a")
    artifact = db.create_artifact_metadata(
        session_id="session-artifact",
        artifact_id="artifact-1",
        artifact_type="screenshot",
        media_type="image/png",
        storage_path=str(artifact_dir / "artifact-1.png"),
        size_bytes=12,
        checksum="abc123",
        event_id=7,
    )

    artifacts = db.list_artifacts(session_id="session-artifact")

    assert artifact["artifact_id"] == "artifact-1"
    assert artifacts == [artifact]
    assert artifacts[0]["user_id"] == "user-a"
    assert artifacts[0]["organization_id"] == "org-a"


def test_screenshot_artifact_writes_local_file(tmp_path, monkeypatch):
    db_path = tmp_path / "screenshot-artifact.db"
    artifact_dir = tmp_path / "artifacts"
    image_bytes = b"fake png bytes"
    monkeypatch.setenv("COMPUTER_USE_DB_PATH", str(db_path))
    monkeypatch.setenv("ARTIFACT_STORAGE_DIR", str(artifact_dir))

    db.init_db()
    db.insert_session("session-screenshot", user_id="user-a", organization_id="org-a")
    event_id = db.insert_event("session-screenshot", "screenshot", {"image_base64": "kept-inline"})
    artifact = db.create_screenshot_artifact(
        "session-screenshot",
        event_id,
        {"image_base64": base64.b64encode(image_bytes).decode("ascii")},
    )

    assert artifact is not None
    assert artifact["event_id"] == event_id
    assert artifact["size_bytes"] == len(image_bytes)
    assert artifact["checksum"]
    assert artifact["storage_path"]
    assert artifact_dir.exists()
    assert artifact["storage_path"].endswith(".png")


def test_cleanup_retention_prunes_expired_rows(tmp_path, monkeypatch):
    now = time.time()
    db_path = tmp_path / "retention.db"
    monkeypatch.setenv("COMPUTER_USE_DB_PATH", str(db_path))
    monkeypatch.setenv("MESSAGE_RETENTION_DAYS", "1")
    monkeypatch.setenv("EVENT_RETENTION_DAYS", "1")
    monkeypatch.setenv("SCREENSHOT_RETENTION_DAYS", "1")

    db.init_db()
    db.insert_session("session-retention")
    conn = db.get_conn()
    old_ts = now - (2 * 86400)
    conn.execute(
        "INSERT INTO messages (session_id, role, text, ts) VALUES (?, ?, ?, ?)",
        ("session-retention", "user", "old", old_ts),
    )
    conn.execute(
        "INSERT INTO events (session_id, event, data, ts) VALUES (?, ?, ?, ?)",
        ("session-retention", "old_event", "{}", old_ts),
    )
    conn.commit()
    conn.close()
    db.create_artifact_metadata(
        session_id="session-retention",
        artifact_id="artifact-expired",
        artifact_type="screenshot",
        media_type="image/png",
        expires_at=now - 1,
    )

    dry_run = db.cleanup_retention(dry_run=True, now=now)
    assert dry_run["messages"] == 1
    assert dry_run["events"] == 1
    assert dry_run["artifacts"] == 1
    assert db.get_session_history("session-retention")["messages"]
    assert db.list_artifacts(session_id="session-retention")

    applied = db.cleanup_retention(dry_run=False, now=now)

    assert applied["messages"] == 1
    assert applied["events"] == 1
    assert applied["artifacts"] == 1
    history = db.get_session_history("session-retention")
    assert history["messages"] == []
    assert history["events"] == []
    assert db.list_artifacts(session_id="session-retention") == []
    deleted_artifacts = db.list_artifacts(session_id="session-retention", include_deleted=True)
    assert deleted_artifacts[0]["deleted_at"] is not None
