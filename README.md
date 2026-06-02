# Claude Computer Use Session Orchestrator

A session-oriented FastAPI backend for running isolated Claude Computer Use
workers with real-time event streaming, noVNC desktop access, Docker-based
worker lifecycle management, and persistent session history.

This project explores how Operator-style computer-use agents can be managed as
backend workloads instead of as a single-user demo. Each session gets its own
desktop worker, can be observed through noVNC, streams progress through SSE, and
stores messages/events for later debugging.

> Prototype status: production-style architecture and tests, but not hardened
> for untrusted or public deployments.

## Highlights

- Isolated per-session worker containers managed by a FastAPI orchestrator
- Real-time Server-Sent Events for agent progress, screenshots, tool calls, and
  completion/error states
- Browser-accessible noVNC desktop for observing each running worker
- SQLite-backed session, message, status, error, and event persistence
- Dependency-free HTML/CSS/JavaScript frontend for local demos
- Focused backend tests with mocked worker behavior
- Reuses Anthropic Computer Use loop/tools instead of reimplementing the agent
  runtime

## Why This Exists

Computer-use agents become more useful when they can be started, isolated,
observed, stopped, and debugged like real backend workloads. The original demo
stack is valuable for experimentation, but it is centered around one local
session. This repository wraps that idea with a small orchestration layer:

- create and delete sessions through an API
- allocate a dedicated Docker worker for each session
- forward user tasks to the worker API
- stream live worker events back to the frontend
- persist history so completed sessions can be inspected later
- expose each worker desktop through noVNC

The goal is not to claim this is a finished platform. The goal is to show the
backend shape needed to move computer-use agents toward multi-session,
observable workflows.

## Architecture

```text
HTML/JS frontend
    |
    | REST + SSE
    v
FastAPI orchestrator
    |
    | Docker worker lifecycle
    v
Per-session worker container
    |
    | Anthropic Computer Use loop/tools
    v
Virtual desktop + noVNC + worker events

SQLite stores sessions, messages, statuses, errors, and event history.
```

The primary interface is the dependency-free frontend under `web/`. The
Streamlit code is retained only as legacy/debug reference code and is not part
of the main flow.

## Tech Stack

- Python
- FastAPI
- Docker
- SQLite
- Server-Sent Events
- VNC / noVNC
- Anthropic Claude Computer Use stack
- HTML, CSS, JavaScript
- pytest

## Repository Structure

```text
.
├── computer_use_demo/
│   ├── api/
│   │   ├── main.py              # FastAPI orchestrator
│   │   ├── db.py                # SQLite persistence helpers
│   │   └── worker_manager.py    # Docker worker lifecycle
│   ├── worker_api.py            # Primary worker FastAPI API
│   ├── worker_api_service/      # Lightweight echo/SSE stub for experiments
│   ├── loop.py                  # Anthropic Computer Use sampling loop
│   ├── streamlit.py             # Legacy/debug UI, not primary flow
│   └── tools/                   # Computer, bash, edit, and run tools
├── demo/
│   └── concurrency_demo.sh      # Manual multi-session demo helper
├── image/                       # Worker desktop/noVNC startup scripts
├── tests/                       # Backend and worker tests
├── web/                         # Primary HTML/JS frontend
├── Dockerfile                   # Worker image
├── Dockerfile.orchestrator      # Orchestrator image
├── docker-compose.yml
├── requirements.txt
├── dev-requirements.txt
├── ruff.toml
├── pyproject.toml
└── .env.example
```

## Setup

Create a Python environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install -r dev-requirements.txt
```

Export the required environment variables:

```bash
export ANTHROPIC_API_KEY="your_anthropic_api_key"
export COMPUTER_USE_DB_PATH="./data/orchestrator.db"
export PUBLIC_HOST="127.0.0.1"
export WORKER_CONNECT_HOST="127.0.0.1"
export MODEL="claude-sonnet-4-5-20250929"
export TOOL_VERSION="computer_use_20250124"
export MAX_TOKENS="4096"
export ENABLE_STREAMLIT="false"
```

Build the worker image:

```bash
docker build -t computer-use-demo:local .
```

Start the orchestrator:

```bash
python -m uvicorn computer_use_demo.api.main:app --host 127.0.0.1 --port 9000
```

Start the frontend in another terminal:

```bash
python -m http.server 5173 -d web
```

Open the app:

```text
http://127.0.0.1:5173
```

## Docker Compose

The compose setup runs the orchestrator and static frontend. Worker containers
are still created dynamically by the orchestrator, one per session.

```bash
export ANTHROPIC_API_KEY="your_anthropic_api_key"
docker build -t computer-use-demo:local .
docker compose up --build
```

Open:

```text
http://127.0.0.1:5173
```

The orchestrator container mounts the Docker socket so it can create worker
containers. This is practical for local development, but it should be hardened
before use in untrusted environments.

## Usage

1. Open the frontend.
2. Click `New Session`.
3. Select the session in the sidebar.
4. Click `Open noVNC` to observe the worker desktop.
5. Send a task such as:

```text
Open Firefox and search for the current weather in Tokyo.
```

6. Watch real-time events in the frontend:

```text
user_message
assistant_block
tool_use_start
tool_result
screenshot
done
error
```

7. Refresh the browser and click `History` to reload persisted events.
8. Create a second session to verify independent worker containers.

The frontend stores recent session IDs in local browser storage. Use
`Clear local` if the backend has been restarted and old sessions no longer
exist.

## API Overview

```http
POST   /sessions
GET    /sessions/{id}
DELETE /sessions/{id}

POST   /sessions/{id}/messages
GET    /sessions/{id}/events
GET    /sessions/{id}/history
```

`POST /sessions` returns:

- `session_id`
- `novnc_url`
- `ui_url`
- `worker_http`

`GET /sessions/{id}/events` streams worker events through SSE.

`GET /sessions/{id}/history` returns persisted session metadata, messages, and
events from SQLite.

## Testing

Run the focused backend suite:

```bash
python -B -m pytest -q tests/test_api_app.py tests/test_db.py tests/test_orchestrator_sessions.py tests/test_worker_api.py
```

Run all tests:

```bash
pytest
```

The worker tests use mocks and do not call the real Anthropic API.

## Demo Flow

A concise five-minute portfolio demo:

1. Show the architecture diagram.
2. Start Docker, the orchestrator, and the frontend.
3. Create Session A.
4. Open noVNC for Session A.
5. Send a browser/search task.
6. Show live SSE events and desktop activity.
7. Create Session B and send a different task.
8. Show both sessions have independent containers.
9. Refresh the frontend and load `History`.
10. Show the focused tests passing.

## Known Limitations

- SQLite is used for local/demo persistence.
- Active worker reattachment after orchestrator restart is not fully
  implemented.
- Docker socket mounting is convenient locally but requires hardening in
  production-like deployments.
- Real Claude execution requires a valid Anthropic API key.
- The frontend is intentionally basic and optimized for demonstrating APIs.
- Authentication and authorization are not included.

## Future Improvements

- PostgreSQL persistence
- Worker reattachment and recovery after orchestrator restart
- Authentication and per-user authorization
- Queue-based scheduling for tasks and workers
- Kubernetes deployment model
- Richer frontend with screenshots and task timelines
- WebSocket streaming alternative
- Structured observability with metrics and tracing

## Security Notes

- Never commit `.env` or real API keys.
- Do not expose the Docker socket in untrusted environments.
- API keys are passed through environment variables to worker containers.
- noVNC ports are bound locally by default; review network exposure before
  deploying remotely.
