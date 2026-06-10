# SaaS Evolution

This repo started as a local Claude Computer Use orchestration prototype and was
incrementally shaped toward a SaaS architecture. The goal was not to rewrite the
system, but to add production boundaries around the existing working flow.

## Preserved Core Flow

```text
Frontend -> FastAPI orchestrator -> WorkerLauncher -> Docker worker
         -> Claude Computer Use -> SSE/noVNC -> SQLite/Postgres history
```

## Phase Summary

| Phase | Boundary Added | Notes |
| --- | --- | --- |
| 1 | Auth and tenancy foundation | Local dev identity, users, orgs, memberships, session ownership checks. |
| 2 | Limits and lifecycle | Concurrent limits, runtime/idle expiration, message/event caps, kill switches. |
| 3 | Protected UI access | Ownership-checked noVNC route and optional signed temporary UI tokens. |
| 4 | WorkerLauncher | Docker lifecycle moved behind a launcher interface while preserving local Docker. |
| 5 | Observability | Request IDs, readiness, metrics, and admin safety visibility. |
| 6 | Production database path | PostgreSQL support and Alembic migrations, with SQLite still default. |
| 7 | Retention foundation | Soft delete, artifact metadata, local screenshot files, dry-run cleanup reports. |
| 8 | Documentation polish | Clear repository positioning, demo flow, and operational docs. |
| 9 | Release readiness | Final docs, command, security, git hygiene, and verification pass. |

## What Is SaaS-Shaped Today

- Tenant ownership is enforced on session-scoped APIs.
- Sessions have explicit lifecycle status and safety limits.
- Worker access is mediated by the orchestrator.
- Persistence has a migration path.
- Operators have readiness, metrics, and admin visibility.
- Retention policy has explicit configuration and dry-run reporting.

## What Is Still Prototype/Local

- Auth is a local adapter, not OIDC or hosted auth.
- `local_docker` uses the local Docker socket.
- noVNC still ultimately reaches local worker ports.
- Artifacts are local files, not object storage.
- Metrics are JSON snapshots, not a full monitoring stack.
- The frontend is a demo console.
- The project is release-ready as a production-style prototype, not a hosted
  SaaS service.

## Next Production Steps

1. Replace local auth with a real identity provider and admin roles.
2. Replace direct Docker access with a remote/internal worker launcher.
3. Move artifacts to object storage with signed object URLs.
4. Add cost accounting for provider tokens and worker runtime.
5. Add deployment, TLS, secrets management, and observability backend.
6. Add worker reattachment/reconciliation after orchestrator restart.
