# Worker Isolation

## Problem

Computer-use agents need desktop state and tools, but those tools should not
share process, port, or filesystem state across user sessions.

## Goals

- Keep one worker container per session.
- Preserve CPU, memory, and PID limits.
- Bind worker ports locally for the prototype.
- Keep Docker-specific behavior behind WorkerLauncher.
- Document future remote launcher options.

## Non-Goals

- Kubernetes implementation.
- Fargate/Fly Machines implementation.
- Strong production sandboxing.
- Public reverse proxy for noVNC.

## Architecture

- `WorkerLauncher` defines the lifecycle contract.
- `LocalDockerWorkerLauncher` implements the current Docker behavior.
- Workers expose message, event, status, and noVNC endpoints to the
  orchestrator.
- The orchestrator mediates user access to UI routes.

## Data Flow

1. Orchestrator allocates ports.
2. Launcher starts a labeled Docker container.
3. Orchestrator waits for readiness.
4. Worker receives goals through its HTTP message API.
5. Worker streams events back over SSE.
6. Stop/delete calls terminate the container.

## Edge Cases

- Port allocation conflict.
- Docker daemon unavailable.
- Worker readiness timeout.
- Orphaned worker from a previous run.
- User tries to access raw noVNC URL without ownership/token checks.

## Acceptance Criteria

- WorkerLauncher can be mocked in tests.
- Local Docker behavior remains unchanged.
- Orphan cleanup delegates to launcher.
- Docs clearly call Docker socket access a local trust boundary.
