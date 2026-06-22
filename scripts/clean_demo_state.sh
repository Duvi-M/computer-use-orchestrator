#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "Cleaning demo/runtime state only..."

rm -f data/task_queue.db
rm -f data/interview_task_queue.db
rm -f data/task_queue_smoke.db
rm -f data/agent_harness.start
rm -f data/agent_harness_smoke.start
rm -f data/interview_harness_memory.json
rm -f data/harness_memory.json

find data/checkpoints -maxdepth 1 -type f -name "*.json" -delete 2>/dev/null || true
find data/interview_checkpoints -maxdepth 1 -type f -name "*.json" -delete 2>/dev/null || true

rm -rf data/interview_session_harness_traces
rm -rf data/traces/demo_parallel_workflows
rm -rf data/traces/session_harness

find . -path "./.venv" -prune -o -type d -name "agent_outputs" -exec rm -rf {} + 2>/dev/null || true
rm -rf worktrees

find . -path "./.venv" -prune -o -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
rm -rf .pytest_cache
rm -rf .ruff_cache

echo "Demo state cleaned. Source, specs, docs, and .venv were preserved."
