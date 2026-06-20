#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <tmux-session-name> <goal-id> <goal text...>" >&2
  exit 64
fi

SESSION_NAME="$1"
GOAL_ID="$2"
shift 2
GOAL_TEXT="$*"

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is required but was not found in PATH" >&2
  exit 127
fi

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  echo "Attaching to existing tmux session: $SESSION_NAME"
  exec tmux attach-session -t "$SESSION_NAME"
fi

PYTHON_BIN="${PYTHON:-python3}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNNER_CMD=(
  "$PYTHON_BIN"
  -m computer_use_demo.harness.runner
  --goal-id "$GOAL_ID"
  --goal-text "$GOAL_TEXT"
)

tmux new-session -d -s "$SESSION_NAME" -c "$REPO_ROOT" "$(printf '%q ' "${RUNNER_CMD[@]}")"
echo "Created tmux session: $SESSION_NAME"
exec tmux attach-session -t "$SESSION_NAME"
