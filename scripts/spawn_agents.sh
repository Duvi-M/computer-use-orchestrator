#!/usr/bin/env bash
set -euo pipefail

AGENT_COUNT="${1:-3}"
SESSION_NAME="${TMUX_SESSION_NAME:-agent-harness}"
QUEUE_DB="${TASK_QUEUE_DB:-data/task_queue.db}"
SEED_TASKS="${SEED_TASKS:-18}"
PYTHON_BIN="${PYTHON:-python3}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
START_SIGNAL="${AGENT_START_SIGNAL:-data/agent_harness.start}"
ATTACH="${ATTACH:-true}"

if ! [[ "$AGENT_COUNT" =~ ^[0-9]+$ ]] || [[ "$AGENT_COUNT" -lt 1 ]]; then
  echo "Usage: $0 [agent-count>=1]" >&2
  exit 64
fi

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is required but was not found in PATH" >&2
  exit 127
fi

if ! [[ "$SEED_TASKS" =~ ^[0-9]+$ ]]; then
  echo "SEED_TASKS must be an integer >= 0" >&2
  exit 64
fi

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  echo "Attaching to existing tmux session: $SESSION_NAME"
  exec tmux attach-session -t "$SESSION_NAME"
fi

mkdir -p "$REPO_ROOT/worktrees"
mkdir -p "$(dirname "$REPO_ROOT/$START_SIGNAL")"
rm -f "$REPO_ROOT/$START_SIGNAL"

if [[ "$SEED_TASKS" -gt 0 ]]; then
  PYTHONPATH="$REPO_ROOT" "$PYTHON_BIN" - "$REPO_ROOT/$QUEUE_DB" "$SEED_TASKS" <<'PY'
from pathlib import Path
import sys

from computer_use_demo.harness.shared_task_queue import enqueue_task

queue_db = Path(sys.argv[1])
count = int(sys.argv[2])
for index in range(1, count + 1):
    enqueue_task({"kind": "demo", "description": f"demo task {index}"}, queue_db)
print(f"Seeded {count} demo tasks in {queue_db}")
PY
fi

ensure_worktree() {
  local index="$1"
  local path="$REPO_ROOT/worktrees/agent-$index"
  local branch="agent/agent-$index"

  if [[ -d "$path/.git" ]] || [[ -f "$path/.git" ]]; then
    echo "$path"
    return
  fi

  if git -C "$REPO_ROOT" show-ref --verify --quiet "refs/heads/$branch"; then
    git -C "$REPO_ROOT" worktree add "$path" "$branch" >/dev/null
  else
    git -C "$REPO_ROOT" worktree add -b "$branch" "$path" HEAD >/dev/null
  fi
  echo "$path"
}

worker_command() {
  local agent_id="$1"
  local worktree="$2"
  printf '%q ' \
    "$PYTHON_BIN" \
    "$REPO_ROOT/scripts/agent_worker.py" \
    --agent-id "$agent_id" \
    --worktree "$worktree" \
    --queue-db "$REPO_ROOT/$QUEUE_DB" \
    --start-signal "$REPO_ROOT/$START_SIGNAL"
}

FIRST_WORKTREE="$(ensure_worktree 1)"
tmux new-session -d -s "$SESSION_NAME" -c "$FIRST_WORKTREE" "$(worker_command agent-1 "$FIRST_WORKTREE")"

for index in $(seq 2 "$AGENT_COUNT"); do
  WORKTREE_PATH="$(ensure_worktree "$index")"
  tmux split-window -t "$SESSION_NAME" -c "$WORKTREE_PATH" "$(worker_command "agent-$index" "$WORKTREE_PATH")"
  tmux select-layout -t "$SESSION_NAME" tiled >/dev/null
done

for _ in $(seq 1 50); do
  PANE_COUNT="$(tmux list-panes -t "$SESSION_NAME" | wc -l | tr -d ' ')"
  if [[ "$PANE_COUNT" == "$AGENT_COUNT" ]]; then
    break
  fi
  sleep 0.1
done

touch "$REPO_ROOT/$START_SIGNAL"

echo "Started $AGENT_COUNT agent panes in tmux session: $SESSION_NAME"
echo "Queue DB: $REPO_ROOT/$QUEUE_DB"
echo "Start signal: $REPO_ROOT/$START_SIGNAL"
if [[ "$ATTACH" == "false" ]]; then
  echo "Attach skipped because ATTACH=false"
  exit 0
fi
exec tmux attach-session -t "$SESSION_NAME"
