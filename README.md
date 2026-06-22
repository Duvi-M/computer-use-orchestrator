# Agentic Harness for Computer-Use Agents

Spec-driven control plane for computer-use agents: goals become execution
contracts, plans, bounded actions, observations, evidence, eval-gate decisions,
memory records, traces, and escalation paths.

The primary story is the harness:

```text
Spec -> ExecutionContract -> AgentLoopState
     -> Worker Events -> Observation/Evidence
     -> EvalGates -> Traces/Memory
     -> Next Step / Escalation
```

The FastAPI/Docker/noVNC system remains as a real runtime backend surface for
Claude Computer Use sessions. It is useful because the harness can consume
real worker-style events, but it is not the whole product story.

This is not a hosted SaaS yet. It is a production-style agentic harness and
runtime backend prototype built to make agent execution observable, bounded,
recoverable, and evidence-driven.

## What This Is

This repository demonstrates how to scaffold autonomous computer-use agents:

- spec-driven feature definitions in custom spec format and manually written
  GitHub Spec Kit-style `spec.md`/`plan.md`/`tasks.md` files
- `goal -> plan -> action -> observation -> evidence -> evaluation` loop
- execution contracts with required outputs, budgets, grants, completion
  conditions, and escalation policy
- eval gates so completion depends on evidence, not self-reporting
- file-backed local memory with optional mem0 backend
- durable raw traces for replay, debugging, and evals
- tmux/checkpoint persistence for long-running local agent loops
- parallel worktree-isolated agents coordinated by a shared SQLite task queue
- FastAPI/Docker worker runtime as a secondary surface for real Computer Use

It is intentionally not just an API wrapper around Claude. The repo models the
control plane around execution: specify, start, observe, constrain, persist,
evaluate, remember, and decide what should happen next.

## Project Status

Current status: production-style agentic harness prototype.

- Works locally end to end: browser frontend, FastAPI orchestrator, Docker
  worker, Claude Computer Use, SSE events, noVNC, and persisted history.
- Harness and runtime foundations are implemented: specs, loop state,
  contracts, budgets, eval gates, memory, traces, triggers, tmux persistence,
  parallel queue demos, worker event adapter, and FastAPI/Docker runtime
  integration.
- Not yet implemented: hosted auth, remote worker launcher, object storage,
  deployment hardening, billing, compliance controls, and production admin
  roles.

## BOS.PRO Requirement Mapping

| Requirement | Project Evidence | Status |
| --- | --- | --- |
| Spec-Driven Dev | `specs/`, `specs/spec-kit/`, `.specify/`, `specs/001-multi-agent-orchestration/`, `docs/INTERVIEW_DEMO.md` | Implemented: custom specs plus manually written GitHub Spec Kit-style files; additionally verified with the official GitHub Spec Kit CLI via `specify init --here --force --integration claude` and `/speckit.specify`, producing `.specify/` and `specs/001-multi-agent-orchestration/spec.md` |
| Agentic Scaffolding | `computer_use_demo/harness/` | Implemented |
| Goal/Plan/Action Loop | `loop.py`, `runner.py`, `SessionHarness` | Implemented |
| Execution Contracts | `contracts.py`, `ExecutionContract` | Implemented |
| Budgets | `budgets.py`, API session limits | Implemented |
| Eval Gates | `eval_gates.py`, `evals/run_eval.py` | Implemented |
| Memory Layer | `memory.py` file-backed memory, mem0 optional | Implemented: file-backed local memory verified live with keyword recall; mem0 backend is wired but only auto-activates with a valid OpenAI key and is not yet exercised end-to-end in the live demo |
| Traces | `traces.py`, `SessionHarness` trace output | Implemented |
| tmux persistence | `run_harness_tmux.sh`, checkpoints, tmux-resurrect/continuum | Verified live outside sandbox: `harness-demo` runner session restored after a real macOS reboot using tmux-resurrect + tmux-continuum, with `data/checkpoints/tokyo-run.json` intact |
| Parallel agents | `interview_demo.py agents`, `spawn_agents.sh` | Implemented: 6 agents (>5) verified live via `interview_demo.py`'s thread-based demo with task distribution across all agents and zero duplicate claims; 3-agent tmux/worktree version also verified separately; 10+ agent / 100+ task load testing and production-grade fairness metrics remain future work |
| Worktree isolation | `spawn_agents.sh` creates `worktrees/agent-N` | Implemented for the local demo with git worktrees; production code-writing reconciliation remains future work |
| Shared task queue | `shared_task_queue.py` with `BEGIN IMMEDIATE` | Implemented locally with SQLite single-writer claims; distributed or multi-host queueing remains future work |
| FastAPI/Docker runtime | `computer_use_demo/api/`, `WorkerLauncher` | Implemented as runtime backend |

Additional external harness evidence: Claude Code Agent Teams was tested outside
the repo's runtime path with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`: three
Claude Code agents ran in separate git worktrees using Claude Code's native
shared task list to audit tests, spec/code consistency, and documentation
contradictions. This was an isolated learning/evidence exercise; it is not
integrated into this repository's harness runtime.

## Why This Is A Harness

Computer-use agents are expensive, stateful, and operationally risky. They need
more than a chat endpoint: they need worker isolation, session lifecycle
controls, event streaming, desktop access, auditability, retention policy, and
clear security boundaries. This repo keeps those concerns visible without
prematurely adding Kubernetes, queues, billing, or a frontend framework.

Harness responsibilities represented here:

- session lifecycle from create/start/ready/run/complete/fail/delete
- isolated one-worker-per-session execution
- SSE event stream and persisted history
- runtime, idle, message, and event budgets
- execution contracts and durable raw traces
- tool grant and eval-gate primitives
- dynamic workflow pattern docs
- protected noVNC access
- worker launcher abstraction
- observability and admin safety visibility

## What Works Today

- FastAPI orchestrator with session, message, history, health, readiness,
  metrics, admin, UI-token, and retention endpoints.
- Dependency-free HTML/JS demo frontend.
- One local Docker worker container per session.
- Claude Computer Use execution inside the worker.
- SSE event proxying and persistence.
- noVNC desktop access through ownership-checked orchestrator URLs.
- Local dev auth adapter with users, organizations, memberships, and ownership
  checks.
- Session limits, runtime/idle expiration, message/event quotas, kill switches,
  and worker cleanup.
- Worker lifecycle behind a `WorkerLauncher` protocol with
  `LocalDockerWorkerLauncher`.
- SQLite default persistence plus PostgreSQL/Alembic production path.
- Artifact metadata and retention cleanup foundation.
- Harness primitives for goals, plans, actions, observations, evidence, eval
  gates, escalation decisions, execution contracts, budgets, tool grants,
  traces, and triggers.
- `SessionHarness` adapter that maps real worker-style events into
  observations, evidence, eval-gate results, and durable traces.
- Local file-backed harness memory for recording and recalling evidence by
  keyword, with optional mem0 backend only when a valid OpenAI key is present.
- Offline eval and safe parallel-session/parallel-workflow demo scripts.
- Focused tests for auth, limits, UI tokens, launcher behavior, observability,
  database config, migrations, retention, harness primitives, and worker APIs.

## Harness Architecture

```mermaid
flowchart LR
    Spec["Spec / Feature Intent"] --> Contract["ExecutionContract"]
    Contract --> State["AgentLoopState"]
    State --> Plan["Goal / Plan / Action"]
    Plan --> Runtime["Worker Events"]
    Runtime --> Obs["Observation"]
    Runtime --> Ev["Evidence"]
    Obs --> Gates["EvalGates"]
    Ev --> Gates
    Gates --> Trace["RawTrace / TraceStore"]
    Gates --> Memory["HarnessMemory"]
    Gates --> Decision["Next Step / Escalation"]
```

More detail: [docs/HARNESS_ARCHITECTURE.md](docs/HARNESS_ARCHITECTURE.md).

## Runtime Backend: FastAPI + Docker Workers

The runtime backend is the secondary surface that gives the harness real
computer-use events to observe. It preserves the existing local demo:

```mermaid
flowchart LR
    Browser["Browser frontend<br/>HTML / JS"] -->|"REST"| API["FastAPI orchestrator"]
    Browser -->|"SSE events"| API
    Browser -->|"Open noVNC"| UI["/sessions/{id}/ui<br/>ownership/token checked"]

    API --> Auth["Local auth / tenancy<br/>X-User-Id + X-Org-Id"]
    API --> Limits["Session limits<br/>quotas + lifecycle"]
    API --> DB[("SQLite local<br/>or PostgreSQL")]
    API --> Retention["Retention cleanup<br/>artifact metadata"]
    API --> Launcher["WorkerLauncher protocol"]

    Launcher --> LocalDocker["LocalDockerWorkerLauncher"]
    LocalDocker --> Docker["Docker Engine"]
    Docker --> Worker["One worker container<br/>per session"]

    Worker --> Claude["Claude Computer Use<br/>loop + tools"]
    Worker --> Desktop["Virtual desktop<br/>VNC / noVNC"]
    Worker -->|"SSE"| API
    Worker -->|"screenshots/events"| API

    Retention --> Artifacts["Local artifact storage<br/>future S3/object store"]
    UI --> Desktop
```

Text flow:

```text
Frontend -> FastAPI orchestrator -> WorkerLauncher -> Docker worker
         -> Claude Computer Use -> SSE/noVNC -> SQLite/Postgres history
```

## Agent Loop

The current Claude Computer Use loop still runs inside the worker. The harness
now exposes the surrounding control model in `computer_use_demo/harness/`:

```text
goal -> plan -> action -> observation/evidence -> evaluation -> next step/escalation
```

Implemented primitives:

- `Goal`, `Plan`, `AgentAction`
- `Observation`, `Evidence`
- `EvalGate`, `EvalGateResult`
- `EscalationDecision`
- `TriggerDispatcher`

These primitives are intentionally lightweight. They document the contract and
support tests/evals without replacing the worker execution path.

For a bounded CLI demo of the durable loop:

```bash
python3 -m computer_use_demo.harness.runner \
  --goal-id tokyo-run \
  --goal-text "search Tokyo weather" \
  --interval-seconds 0.1 \
  --max-iterations 8
```

The runner checkpoints state frequently under `data/checkpoints/`, but only
records semantic memory when evidence content changes. Repeated checkpoint
ticks do not create duplicate memory entries.

## Execution Contracts

`ExecutionContract` makes each task/session explicit before work starts:

- required outputs
- runtime/message/event/token/cost budgets
- permissions/tool grants
- completion conditions
- output/evidence paths
- escalation policy

This is the core harness principle: the agent does not execute freely. It runs
inside a contract that can be checked by budget logic, eval gates, durable
traces, and human escalation.

## Session Lifecycle

Sessions move through explicit statuses such as `created`, `starting`, `ready`,
`running`, `completed`, `failed`, `stopped`, `expired`, `deleted`, and `killed`.
The orchestrator enforces ownership, lifecycle validity, runtime/idle expiry,
message limits, event limits, and worker cleanup.

Lifecycle events are persisted so an operator can inspect what happened after a
session stops. Deletes are logical first; retained history is cleaned later by
retention policy.

## Worker Isolation

The invariant is one worker container per session. `LocalDockerWorkerLauncher`
preserves local Docker behavior behind the `WorkerLauncher` protocol:

- local port allocation
- container labels
- readiness checks
- CPU, memory, and PID limits
- worker message/event/status/noVNC metadata
- orphan cleanup

The local Docker socket is still a trusted-development boundary. Production
should replace it with a remote/internal launcher.

## Budgets And Safety

Implemented budgets:

- concurrent sessions per user/org
- max runtime
- max idle time
- max messages per session
- max events per session
- platform/global kill switches

Harness placeholders:

- token budget
- provider cost budget

Budget failures are represented as quota/lifecycle events and can drive trigger
or escalation policy.

## Tool Grants

`computer_use_demo/harness/tool_grants.py` models session-level grants for:

- browser
- shell
- file system
- desktop/computer-use
- network

The current worker remains trusted local demo infrastructure; this grant model
is the explicit contract for future enforcement and review.

## Durable Traces

`TraceStore` writes raw JSON traces under a caller-provided directory, typically
`data/traces/...` for local demos. Traces can include:

- session id and goal
- actions
- observations
- tool calls/events
- budget usage
- final status and failure reason
- evidence/artifact paths

This gives the harness file-backed state for debugging, restarts, evals, and
partial replay. The production roadmap is to back traces with durable storage
and stronger retention controls.

## Evals

The `evals/` directory contains a safe offline benchmark shape:

```bash
python3 evals/run_eval.py --json
```

It simulates session creation, worker readiness, goal execution, evidence
recording, eval gates, budgets, triggers, and session finish. It does not call
Anthropic, launch Docker, or require Postgres.

## Interview Demo CLI

For the 10-minute live interview path, use:

```bash
python3 scripts/interview_demo.py map
python3 scripts/interview_demo.py loop
python3 scripts/interview_demo.py memory
python3 scripts/interview_demo.py eval
python3 scripts/interview_demo.py session-harness
python3 scripts/interview_demo.py agents
```

Full guide: [docs/INTERVIEW_DEMO.md](docs/INTERVIEW_DEMO.md).

| Vacancy signal | Repo area | Demo command |
| --- | --- | --- |
| Spec-driven development | `specs/` and `specs/spec-kit/` | `python3 scripts/interview_demo.py map` |
| Agentic loop | `computer_use_demo/harness/runner.py` | `python3 scripts/interview_demo.py loop` |
| Memory | `computer_use_demo/harness/memory.py` | `python3 scripts/interview_demo.py memory` |
| Evals | `evals/run_eval.py` | `python3 scripts/interview_demo.py eval` |
| Runtime adapter | `computer_use_demo/harness/session_harness.py` | `python3 scripts/interview_demo.py session-harness` |
| Parallel orchestration | worktrees + shared queue | `python3 scripts/interview_demo.py agents` |

## Dynamic Workflow Patterns

Documented examples live in `examples/workflows/`:

- `classify_and_act`
- `fan_out_and_synthesize`
- `adversarial_verification`
- `generate_and_filter`
- `tournament`
- `loop_until_done`

Implemented today: lightweight contracts, budgets, traces, eval gates, triggers,
file-backed memory, SQLite single-writer task claims, and safe parallel workflow
simulation. Roadmap: live workflow runner, durable distributed queue, explicit
goal graph, temporal knowledge graph memory, independent verifier service, and
production scheduling metrics.

## Verification Strategy

The harness should not accept “done” by assertion alone. Completion should be
evidence-based:

- eval gates check required evidence and terminal loop state
- execution contracts define required outputs
- raw traces retain actions, observations, events, budgets, and failure reasons
- independent verifier workflows are documented for high-risk tasks
- human-in-the-loop escalation is the policy for ambiguous or dangerous actions

Failure modes addressed by the design:

- agent laziness: required outputs and eval gates expose incomplete work
- self-preference: adversarial verification is documented as a separate pattern
- goal drift: the original contract remains durable and reloadable
- premature completion: completion requires evidence, not just a final message
- context exhaustion: traces and persisted state reduce context-window reliance

Prefer narrow retry loops:

```text
attempt -> evaluate -> patch -> retry
```

Do not use dynamic workflows for obvious bugs, small mechanical changes, or
tasks where a direct edit plus tests is simpler and safer.

## SaaS Evolution Summary

The repo evolved from a local prototype into a SaaS-shaped architecture in
incremental phases:

- Identity and tenancy: local dev users, organizations, memberships, and
  session ownership checks.
- Session safety: concurrent limits, runtime/idle expiration, message/event
  caps, kill switches, lifecycle statuses, and worker cleanup.
- Protected UI: ownership-checked noVNC access and optional signed temporary UI
  tokens.
- Worker boundary: `WorkerLauncher` protocol with current local Docker
  implementation and future remote launcher slots.
- Observability: request IDs, readiness, metrics, and internal admin visibility.
- Persistence: SQLite local mode plus PostgreSQL support through Alembic
  migrations.
- Retention: soft-deleted sessions, artifact metadata, screenshot file
  foundation, and dry-run retention cleanup.

See [docs/SAAS_EVOLUTION.md](docs/SAAS_EVOLUTION.md) for the phase-by-phase
boundary notes.

## Local Dev Vs Production

Local/dev by default:

- SQLite via `COMPUTER_USE_DB_PATH`
- local dev identity from `X-User-Id` / `X-Org-Id` or `DEV_USER_ID` /
  `DEV_ORG_ID`
- Docker socket access from the FastAPI process
- worker ports bound to localhost
- no hosted auth provider
- no object storage

Production-oriented foundations already present:

- tenant ownership checks
- PostgreSQL-compatible schema and Alembic migrations
- signed UI access tokens
- session quotas and kill switches
- request IDs and operational endpoints
- retention and artifact metadata
- launcher abstraction for future remote worker backends

Still needed for real hosted SaaS:

- OIDC/Auth0/Clerk/Cognito or equivalent hosted auth
- remote/internal worker launcher instead of direct Docker socket access
- object storage for screenshots/artifacts
- production deployment, TLS, ingress, and secrets management
- stronger sandboxing and network egress policy
- billing/cost ledger and provider usage reconciliation

## Quick Start

Python 3.11 is the safest local development version because the worker image
uses Python 3.11. The local API test environment also works on newer Python
versions where dependencies provide wheels.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r computer_use_demo/requirements.txt
python -m pip install -r dev-requirements.txt

export ANTHROPIC_API_KEY="your_anthropic_api_key"
make build-worker
make run-api
```

`computer_use_demo/requirements.txt` is the main runtime dependency file. It
contains FastAPI, Alembic, SQLAlchemy, psycopg, Anthropic SDK dependencies, and
worker/runtime libraries. The root `requirements.txt` is kept as a compatibility
shim that points to the runtime file.

In another terminal:

```bash
make run-web
```

Open:

```text
http://127.0.0.1:5173
```

## Core Commands

```bash
make test           # focused project tests
make build-worker   # build computer-use-demo:local
make run-api        # FastAPI on 127.0.0.1:9000
make run-web        # static frontend on 127.0.0.1:5173
make db-up          # optional local Postgres
make db-migrate     # Alembic upgrade head
make db-down        # stop optional local Postgres
make smoke-local    # health/readiness/frontend smoke check
make clean-workers  # remove project-labeled worker containers
```

`make db-migrate` uses `PYTHON=.venv/bin/python` by default. To use an already
activated environment, run `make PYTHON=python db-migrate`.

## Release/Demo Checklist

```bash
python3 -B -m pytest -q
node --check web/app.js
make build-worker
make db-migrate
make run-api
make run-web
```

Then open `http://127.0.0.1:5173`, create a session, open noVNC, run the Tokyo
weather task, and inspect `/readyz`, `/metrics`, and `/admin/retention`.

## Database Modes

SQLite is the default:

```bash
unset DATABASE_URL
export COMPUTER_USE_DB_PATH="./data/orchestrator.db"
make run-api
```

PostgreSQL is optional:

```bash
make db-up
export DATABASE_URL="postgresql://orchestrator:orchestrator@127.0.0.1:5432/orchestrator"
make db-migrate
make run-api
```

Migrations live in `migrations/versions/`. SQLite `init_db()` remains for simple
local demo setup; Alembic is the production schema path.

## Worker Launcher Model

`WORKER_LAUNCHER=local_docker` is the only implemented launcher. It preserves
the current one-container-per-session execution path, including local port
allocation, labels, readiness checks, CPU/memory/PID limits, SSE URLs, message
URLs, and noVNC metadata.

Future launcher values are documented roadmap placeholders only:
`ecs_fargate`, `fly_machines`, `remote_launcher`, and `kubernetes`.

## Security Boundaries

- Session-scoped endpoints enforce ownership via user/org identity.
- `ORCHESTRATOR_API_TOKEN` optionally protects API endpoints with bearer auth.
- `/sessions/{id}/ui` is ownership-checked; protected UI mode requires signed
  temporary tokens.
- Worker ports are localhost-bound for the local demo.
- Docker socket access is trusted-local only and should be replaced for hosted
  SaaS.
- Secrets, `.env`, DB files, artifacts, logs, and caches are ignored by git.

More detail: [docs/SECURITY_MODEL.md](docs/SECURITY_MODEL.md).

## Observability

Useful endpoints:

```http
GET /healthz
GET /readyz
GET /metrics
GET /admin/sessions
GET /admin/retention
```

Every HTTP response includes `X-Request-Id`. `LOG_FORMAT=json` enables
single-line JSON logs. Admin endpoints are for trusted local/internal debugging
and must be protected by real admin auth before internet exposure.

## Retention And Artifacts

Session deletion is logical first: deleted sessions receive `deleted_at`, become
hidden from normal ownership checks, and remain available for retention cleanup.

Screenshot events remain inline for frontend compatibility. When screenshot
events include base64 image data, the orchestrator can also write local artifact
files under `ARTIFACT_STORAGE_DIR` and record metadata in the `artifacts` table.
This is a local foundation; production should move bytes to object storage.

`GET /admin/retention` returns a dry-run report. Startup cleanup is disabled by
default with `CLEANUP_RETENTION_ON_STARTUP=false`.

## Environment Reference

Key variables are listed in [.env.example](.env.example). The main groups are:

- API/provider: `ANTHROPIC_API_KEY`, `MODEL`, `TOOL_VERSION`, `MAX_TOKENS`
- local auth: `DEV_USER_ID`, `DEV_ORG_ID`, `ORCHESTRATOR_API_TOKEN`
- persistence: `DATABASE_URL`, `COMPUTER_USE_DB_PATH`
- worker launcher: `WORKER_LAUNCHER`, `WORKER_IMAGE`, `WORKER_CONNECT_HOST`
- UI protection: `PROTECT_SESSION_UI`, `UI_TOKEN_SECRET`,
  `UI_TOKEN_TTL_SECONDS`
- lifecycle limits: `MAX_CONCURRENT_SESSIONS_PER_USER`,
  `MAX_CONCURRENT_SESSIONS_PER_ORG`, `MAX_SESSION_RUNTIME_SECONDS`,
  `MAX_IDLE_SESSION_SECONDS`, `MAX_MESSAGES_PER_SESSION`,
  `MAX_EVENTS_PER_SESSION`, `GLOBAL_KILL_SWITCH`
- retention: `MESSAGE_RETENTION_DAYS`, `EVENT_RETENTION_DAYS`,
  `SCREENSHOT_RETENTION_DAYS`, `WORKER_LOG_RETENTION_DAYS`,
  `DELETED_SESSION_RETENTION_DAYS`, `ARTIFACT_STORAGE_DIR`,
  `CLEANUP_RETENTION_ON_STARTUP`
- harness memory: `HARNESS_MEMORY_USER_ID`, `HARNESS_MEMORY_FILE`,
  `HARNESS_MEMORY_EMBEDDING_MODEL`
- observability: `LOG_LEVEL`, `LOG_FORMAT`

## Demo For Interview

1. Run `make test`.
2. Run `make build-worker`.
3. Start the API: `make run-api`.
4. Start the frontend: `make run-web`.
5. Open `http://127.0.0.1:5173`.
6. Click `Clear local`, then create a session.
7. Click `Open noVNC`.
8. Send a task, for example:

```text
Open a browser, search for the current weather in Tokyo, and tell me the temperature.
```

9. Point out live SSE events: `assistant_block`, `tool_use_start`,
   `tool_result`, `screenshot`, and `done`.
10. Refresh and load `History`.
11. Show `/readyz`, `/metrics`, and `/admin/retention`.
12. Explain SaaS boundaries: local auth adapter, one worker per session,
    PostgreSQL-ready persistence, protected UI tokens, retention metadata, and
    what remains before hosted SaaS.

Optional harness demos:

```bash
python3 evals/run_eval.py --json
python3 scripts/demo_parallel_sessions.py --count 3
python3 scripts/demo_parallel_workflows.py --count 3
```

Longer guide: [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md).

## Testing

```bash
ruff check computer_use_demo tests scripts
python3 -B -m pytest -q
node --check web/app.js
python3 -m py_compile migrations/versions/*.py
```

The default pytest suite does not require a live Postgres server or a real
Anthropic API call.

## Known Limitations

- Not a hosted SaaS deployment.
- No production auth provider or role-based admin authorization yet.
- Local Docker socket access remains a major trust boundary.
- Active worker reattachment after orchestrator restart is incomplete.
- PostgreSQL access is synchronous and minimal; no pooling yet.
- Artifact bytes are local files, not S3/object storage.
- `/metrics` is JSON, not Prometheus format.
- The frontend is a demo console, not a production SaaS UI.
- File-backed harness memory is flat keyword recall; mem0 is wired as an
  optional backend but is not yet exercised end-to-end in the live demo.
- Parallel agent orchestration is verified as a local 6-agent (>5) thread-based
  demo with 24/24 tasks completed and no duplicate claims; the larger 10+
  agent / 100+ task load test from the official Spec Kit success criteria and
  production-grade fairness metrics remain unverified.

## Roadmap

- Hosted auth and role-aware admin APIs.
- Remote/internal worker launcher.
- Object storage for screenshots and artifacts.
- Stronger worker isolation and network egress policy.
- Cost ledger and billing integration.
- Deployment profile with TLS, secrets management, and observability backend.
- Optional Prometheus/OpenTelemetry metrics/tracing.
- Worker reattachment/reconciliation after orchestrator restart.
- Temporal knowledge graph for session/evidence state.
- Explicit goal graph/task graph beyond the current SQLite demo queue.
- Kubernetes launcher as a later worker backend.
- Production-grade multi-agent scheduling with 10+ agent / 100+ task load tests
  and fairness metrics.
- Distributed queue/lock backend for multi-host workers.

## Additional Docs

- [Architecture](docs/ARCHITECTURE.md)
- [Harness Architecture](docs/HARNESS_ARCHITECTURE.md)
- [SaaS Evolution](docs/SAAS_EVOLUTION.md)
- [Security Model](docs/SECURITY_MODEL.md)
- [Operations](docs/OPERATIONS.md)
- [Interview Demo](docs/INTERVIEW_DEMO.md)
- [Demo Script](docs/DEMO_SCRIPT.md)
- [Specs](specs/README.md)
- [Workflow Examples](examples/workflows/)
