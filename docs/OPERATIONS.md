# Operations

These commands are intended for local development and portfolio demos.

## Install

```bash
make install
```

Python 3.11 is the safest version because the worker image uses Python 3.11.

## Run The Local Demo

Terminal 1:

```bash
export ANTHROPIC_API_KEY="your_anthropic_api_key"
make build-worker
make run-api
```

Terminal 2:

```bash
make run-web
```

Open `http://127.0.0.1:5173`.

## Database

SQLite is default:

```bash
unset DATABASE_URL
make run-api
```

Optional local Postgres:

```bash
make db-up
export DATABASE_URL="postgresql://orchestrator:orchestrator@127.0.0.1:5432/orchestrator"
make db-migrate
make run-api
```

Stop local Postgres:

```bash
make db-down
```

## Health And Observability

```bash
curl http://127.0.0.1:9000/healthz
curl http://127.0.0.1:9000/readyz
curl http://127.0.0.1:9000/metrics
curl http://127.0.0.1:9000/admin/retention
```

If `ORCHESTRATOR_API_TOKEN` is set, admin/session-scoped endpoints require:

```bash
curl -H "Authorization: Bearer $ORCHESTRATOR_API_TOKEN" \
  http://127.0.0.1:9000/admin/sessions
```

## Retention

Retention cleanup does not run on startup unless explicitly enabled:

```bash
export CLEANUP_RETENTION_ON_STARTUP=true
make run-api
```

Use `/admin/retention` for a dry-run report. Applied cleanup is available from
code through `cleanup_retention(dry_run=False)`.

## Worker Cleanup

```bash
make clean-workers
```

This removes containers labeled `cambioml=orchestrator`. It does not target
unrelated containers.

Optional startup cleanup:

```bash
export CLEANUP_ORPHAN_WORKERS_ON_STARTUP=true
make run-api
```

## Useful Log Events

- `app_startup`
- `startup_retention_cleanup`
- `session_create_requested`
- `session_created`
- `worker_event_received`
- `screenshot_artifact_recorded`
- `task_completed`
- `task_failed`
- `session_deleted`

## Troubleshooting

- Session creation fails: confirm Docker is running and `make build-worker`
  succeeded.
- API returns 401: unset `ORCHESTRATOR_API_TOKEN` for browser demo mode or use
  an API client with the bearer token.
- noVNC opens but desktop is blank: inspect worker logs with `docker logs`.
- `/readyz` fails in Postgres mode: verify `DATABASE_URL` and run
  `make db-migrate`.
- Artifacts are missing: confirm screenshot events include base64 image data and
  `ARTIFACT_STORAGE_DIR` is writable.
