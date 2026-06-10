# Security Model

This project has explicit local security boundaries, but it is not a hardened
hosted SaaS deployment.

## Implemented Boundaries

- Session-scoped endpoints enforce `user_id` and `organization_id` ownership.
- Local dev identity comes from `X-User-Id` and `X-Org-Id`, with environment
  fallbacks for the browser demo.
- `ORCHESTRATOR_API_TOKEN` can require bearer auth for protected API routes.
- noVNC access goes through `/sessions/{id}/ui`, which checks ownership.
- `PROTECT_SESSION_UI=true` requires signed temporary UI tokens.
- Worker containers use local labels, port allocation, CPU limits, memory
  limits, and PID limits.
- Retention cleanup is disabled on startup by default.
- `.env`, local DBs, local artifacts, logs, virtualenvs, and caches are ignored
  by git.

## Local Trust Assumptions

- The orchestrator runs on a trusted developer machine.
- Docker socket access is trusted-local and powerful.
- Worker ports are bound locally.
- The static frontend does not inject bearer tokens.
- Admin endpoints are for local/internal operator use.

## Sensitive Data

The system may store:

- user prompts and assistant messages
- worker event payloads
- screenshots from the worker desktop
- local artifact files
- worker/container metadata

Screenshots may include private browser state or secrets entered during a task.
Use short screenshot retention in shared environments and do not publish local
artifact directories.

## Not Production Auth

The local auth adapter is intentionally simple. Hosted SaaS should replace it
with an authenticated principal from OIDC or an equivalent provider, then keep
the existing ownership checks behind that dependency.

## Required Before Internet Exposure

- Hosted auth and role-based admin authorization.
- TLS and secure cookie/header handling.
- Remote/internal worker launcher with no public Docker socket exposure.
- Network egress controls for workers.
- Object storage with scoped access for artifacts.
- Secrets manager for API keys and signing secrets.
- Audit logs and retention policy review.
