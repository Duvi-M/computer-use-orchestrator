# Security

The canonical security notes live in [../SECURITY.md](../SECURITY.md).

In short:

- This is a trusted local-development prototype.
- Local dev auth models users and organizations but is not production auth.
- Session-scoped endpoints enforce ownership through user/org membership.
- `ORCHESTRATOR_API_TOKEN` can protect API/admin endpoints in local/internal
  mode.
- `/healthz`, `/readyz`, and `/docs` remain public local diagnostics.
- Worker noVNC/VNC ports are local-first; protected UI mode signs orchestrator
  links but does not remove the local worker-port trust boundary.
- Docker socket access is powerful and should not be exposed to untrusted users.
- Secrets and runtime data are ignored by git.
