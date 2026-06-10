from httpx import ASGITransport, AsyncClient

from computer_use_demo.api import main
from computer_use_demo.api.main import _parse_sse_block, app
from computer_use_demo.api.worker_manager import WorkerInfo


def _fake_worker(session_id: str, suffix: int = 1) -> WorkerInfo:
    return WorkerInfo(
        name=f"worker-{session_id}",
        host="127.0.0.1",
        vnc=5900 + suffix,
        novnc=6080 + suffix,
        streamlit=8501 + suffix,
        http=8080 + suffix,
    )


def test_api_app_imports():
    assert app.title == "Computer Use Backend (Challenge)"


def test_parse_sse_block_with_json_data():
    event, data, event_id = _parse_sse_block(
        'id: 42\nevent: assistant_block\ndata: {"type": "text", "text": "hello"}'
    )

    assert event == "assistant_block"
    assert data == {"type": "text", "text": "hello"}
    assert event_id == "42"


def test_parse_sse_block_with_raw_data():
    event, data, event_id = _parse_sse_block("event: debug\ndata: not json")

    assert event == "debug"
    assert data == {"raw": "not json"}
    assert event_id is None


def test_parse_sse_block_with_multiline_json_data():
    event, data, event_id = _parse_sse_block(
        'id: 7\nevent: tool_result\ndata: {"output": "hello\\nworld"}'
    )

    assert event == "tool_result"
    assert data == {"output": "hello\nworld"}
    assert event_id == "7"


async def test_healthz():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://orchestrator") as client:
        response = await client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"ok": True, "status": "healthy"}


async def test_readyz(tmp_path, monkeypatch):
    monkeypatch.setenv("COMPUTER_USE_DB_PATH", str(tmp_path / "ready.db"))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://orchestrator") as client:
        response = await client.get("/readyz")

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["status"] == "ready"


async def test_session_request_passes_when_token_unset(tmp_path, monkeypatch):
    monkeypatch.delenv("ORCHESTRATOR_API_TOKEN", raising=False)
    monkeypatch.setenv("COMPUTER_USE_DB_PATH", str(tmp_path / "open.db"))
    session_id = "session-open"
    main.SESSIONS.clear()
    main.init_db()
    main.insert_session(session_id)
    main.SESSIONS[session_id] = main.SessionState(session_id=session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://orchestrator") as client:
        response = await client.get(f"/sessions/{session_id}")

    assert response.status_code == 200
    assert response.json()["session_id"] == session_id
    main.SESSIONS.clear()


async def test_session_request_requires_token_when_set(tmp_path, monkeypatch):
    monkeypatch.setenv("ORCHESTRATOR_API_TOKEN", "test-token")
    monkeypatch.setenv("COMPUTER_USE_DB_PATH", str(tmp_path / "protected.db"))
    session_id = "session-protected"
    main.SESSIONS.clear()
    main.init_db()
    main.insert_session(session_id)
    main.SESSIONS[session_id] = main.SessionState(session_id=session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://orchestrator") as client:
        response = await client.get(f"/sessions/{session_id}")

    assert response.status_code == 401
    main.SESSIONS.clear()


async def test_session_request_accepts_valid_bearer_token(tmp_path, monkeypatch):
    monkeypatch.setenv("ORCHESTRATOR_API_TOKEN", "test-token")
    monkeypatch.setenv("COMPUTER_USE_DB_PATH", str(tmp_path / "protected-ok.db"))
    session_id = "session-protected-ok"
    main.SESSIONS.clear()
    main.init_db()
    main.insert_session(session_id)
    main.SESSIONS[session_id] = main.SessionState(session_id=session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://orchestrator") as client:
        response = await client.get(
            f"/sessions/{session_id}",
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 200
    assert response.json()["session_id"] == session_id
    main.SESSIONS.clear()


async def test_healthz_remains_public_when_token_set(monkeypatch):
    monkeypatch.setenv("ORCHESTRATOR_API_TOKEN", "test-token")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://orchestrator") as client:
        response = await client.get("/healthz")

    assert response.status_code == 200
    assert response.json()["ok"] is True


async def test_default_dev_identity_can_create_session(tmp_path, monkeypatch):
    monkeypatch.delenv("ORCHESTRATOR_API_TOKEN", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("COMPUTER_USE_DB_PATH", str(tmp_path / "default-identity.db"))
    main.SESSIONS.clear()
    main.init_db()

    def fake_start_worker(*, session_id, api_key):
        return _fake_worker(session_id)

    async def fake_wait_worker_ready(_worker):
        return None

    monkeypatch.setattr(main, "start_worker", fake_start_worker)
    monkeypatch.setattr(main, "_wait_worker_ready", fake_wait_worker_ready)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://orchestrator") as client:
        response = await client.post("/sessions")

    assert response.status_code == 200
    session_id = response.json()["session_id"]
    owner = main.get_session_owner(session_id)
    assert owner is not None
    assert owner["user_id"] == "dev-user"
    assert owner["organization_id"] == "dev-org"
    main.SESSIONS.clear()


async def test_session_owner_can_access_session(tmp_path, monkeypatch):
    monkeypatch.delenv("ORCHESTRATOR_API_TOKEN", raising=False)
    monkeypatch.setenv("COMPUTER_USE_DB_PATH", str(tmp_path / "same-owner.db"))
    main.SESSIONS.clear()
    main.init_db()
    session_id = "session-owner-ok"
    main.insert_session(session_id, user_id="user-a", organization_id="org-a")
    main.SESSIONS[session_id] = main.SessionState(session_id=session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://orchestrator") as client:
        response = await client.get(
            f"/sessions/{session_id}",
            headers={"X-User-Id": "user-a", "X-Org-Id": "org-a"},
        )

    assert response.status_code == 200
    assert response.json()["session_id"] == session_id
    main.SESSIONS.clear()


async def test_different_user_org_cannot_get_session(tmp_path, monkeypatch):
    monkeypatch.delenv("ORCHESTRATOR_API_TOKEN", raising=False)
    monkeypatch.setenv("COMPUTER_USE_DB_PATH", str(tmp_path / "get-denied.db"))
    main.SESSIONS.clear()
    main.init_db()
    session_id = "session-get-denied"
    main.insert_session(session_id, user_id="user-a", organization_id="org-a")
    main.SESSIONS[session_id] = main.SessionState(session_id=session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://orchestrator") as client:
        response = await client.get(
            f"/sessions/{session_id}",
            headers={"X-User-Id": "user-b", "X-Org-Id": "org-b"},
        )

    assert response.status_code == 404
    main.SESSIONS.clear()


async def test_different_user_org_cannot_send_message(tmp_path, monkeypatch):
    monkeypatch.delenv("ORCHESTRATOR_API_TOKEN", raising=False)
    monkeypatch.setenv("COMPUTER_USE_DB_PATH", str(tmp_path / "message-denied.db"))
    main.SESSIONS.clear()
    main.init_db()
    session_id = "session-message-denied"
    main.insert_session(session_id, user_id="user-a", organization_id="org-a")
    main.SESSIONS[session_id] = main.SessionState(
        session_id=session_id,
        worker=_fake_worker(session_id),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://orchestrator") as client:
        response = await client.post(
            f"/sessions/{session_id}/messages",
            json={"text": "hello"},
            headers={"X-User-Id": "user-b", "X-Org-Id": "org-b"},
        )

    assert response.status_code == 404
    main.SESSIONS.clear()


async def test_different_user_org_cannot_get_history(tmp_path, monkeypatch):
    monkeypatch.delenv("ORCHESTRATOR_API_TOKEN", raising=False)
    monkeypatch.setenv("COMPUTER_USE_DB_PATH", str(tmp_path / "history-denied.db"))
    main.SESSIONS.clear()
    main.init_db()
    session_id = "session-history-denied"
    main.insert_session(session_id, user_id="user-a", organization_id="org-a")
    main.SESSIONS[session_id] = main.SessionState(session_id=session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://orchestrator") as client:
        response = await client.get(
            f"/sessions/{session_id}/history",
            headers={"X-User-Id": "user-b", "X-Org-Id": "org-b"},
        )

    assert response.status_code == 404
    main.SESSIONS.clear()


async def test_different_user_org_cannot_connect_sse(tmp_path, monkeypatch):
    monkeypatch.delenv("ORCHESTRATOR_API_TOKEN", raising=False)
    monkeypatch.setenv("COMPUTER_USE_DB_PATH", str(tmp_path / "sse-denied.db"))
    main.SESSIONS.clear()
    main.init_db()
    session_id = "session-sse-denied"
    main.insert_session(session_id, user_id="user-a", organization_id="org-a")
    main.SESSIONS[session_id] = main.SessionState(
        session_id=session_id,
        worker=_fake_worker(session_id),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://orchestrator") as client:
        response = await client.get(
            f"/sessions/{session_id}/events",
            headers={"X-User-Id": "user-b", "X-Org-Id": "org-b"},
        )

    assert response.status_code == 404
    main.SESSIONS.clear()


async def test_different_user_org_cannot_delete_session(tmp_path, monkeypatch):
    monkeypatch.delenv("ORCHESTRATOR_API_TOKEN", raising=False)
    monkeypatch.setenv("COMPUTER_USE_DB_PATH", str(tmp_path / "delete-denied.db"))
    main.SESSIONS.clear()
    main.init_db()
    session_id = "session-delete-denied"
    main.insert_session(session_id, user_id="user-a", organization_id="org-a")
    main.SESSIONS[session_id] = main.SessionState(
        session_id=session_id,
        worker=_fake_worker(session_id),
    )
    stopped = []
    monkeypatch.setattr(main, "stop_worker", lambda name: stopped.append(name))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://orchestrator") as client:
        response = await client.delete(
            f"/sessions/{session_id}",
            headers={"X-User-Id": "user-b", "X-Org-Id": "org-b"},
        )

    assert response.status_code == 404
    assert stopped == []
    assert session_id in main.SESSIONS
    main.SESSIONS.clear()
