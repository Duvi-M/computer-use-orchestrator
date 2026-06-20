from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from computer_use_demo.harness.shared_task_queue import (  # noqa: E402
    claim_next_task,
    complete_task,
    init_queue,
)


def write_dummy_result(worktree: Path, agent_id: str, task_id: int, payload: dict[str, object]) -> Path:
    output_dir = worktree / "agent_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"task-{task_id}.json"
    output_path.write_text(
        json.dumps(
            {
                "agent_id": agent_id,
                "task_id": task_id,
                "payload": payload,
                "status": "completed",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return output_path


def wait_for_start_signal(start_signal: Path | None, agent_id: str, poll_seconds: float = 0.2) -> None:
    if start_signal is None:
        return

    print(f"agent={agent_id} waiting for start signal {start_signal}", flush=True)  # noqa: T201
    while not start_signal.exists():
        time.sleep(poll_seconds)
    print(f"agent={agent_id} received start signal", flush=True)  # noqa: T201


def run_worker(
    *,
    agent_id: str,
    worktree: Path,
    queue_db: Path,
    idle_sleep_seconds: float,
    work_sleep_min_seconds: float,
    work_sleep_max_seconds: float,
    start_signal: Path | None,
    max_tasks: int | None,
) -> None:
    init_queue(queue_db)
    worktree.mkdir(parents=True, exist_ok=True)
    completed = 0
    print(f"agent={agent_id} worktree={worktree} queue={queue_db}", flush=True)  # noqa: T201
    wait_for_start_signal(start_signal, agent_id)
    while max_tasks is None or completed < max_tasks:
        task = claim_next_task(agent_id, queue_db)
        if task is None:
            print(f"agent={agent_id} idle no pending task", flush=True)  # noqa: T201
            time.sleep(idle_sleep_seconds)
            continue

        print(f"agent={agent_id} claimed task={task.id}", flush=True)  # noqa: T201
        work_seconds = random.uniform(work_sleep_min_seconds, work_sleep_max_seconds)
        print(f"agent={agent_id} working task={task.id} seconds={work_seconds:.2f}", flush=True)  # noqa: T201
        time.sleep(work_seconds)
        output_path = write_dummy_result(worktree, agent_id, task.id, task.payload)
        complete_task(
            task.id,
            {
                "agent_id": agent_id,
                "output_path": str(output_path),
                "worktree": str(worktree),
            },
            queue_db,
        )
        completed += 1
        print(f"agent={agent_id} completed task={task.id} output={output_path}", flush=True)  # noqa: T201


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a demo agent worker against a shared queue")
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--worktree", type=Path, required=True)
    parser.add_argument("--queue-db", type=Path, default=Path("data/task_queue.db"))
    parser.add_argument("--idle-sleep-seconds", type=float, default=2.0)
    parser.add_argument("--work-sleep-min-seconds", type=float, default=1.5)
    parser.add_argument("--work-sleep-max-seconds", type=float, default=3.5)
    parser.add_argument("--start-signal", type=Path)
    parser.add_argument("--max-tasks", type=int)
    args = parser.parse_args()
    if args.idle_sleep_seconds <= 0:
        parser.error("--idle-sleep-seconds must be > 0")
    if args.work_sleep_min_seconds < 0:
        parser.error("--work-sleep-min-seconds must be >= 0")
    if args.work_sleep_max_seconds < args.work_sleep_min_seconds:
        parser.error("--work-sleep-max-seconds must be >= --work-sleep-min-seconds")
    if args.max_tasks is not None and args.max_tasks < 1:
        parser.error("--max-tasks must be >= 1")

    run_worker(
        agent_id=args.agent_id,
        worktree=args.worktree,
        queue_db=args.queue_db,
        idle_sleep_seconds=args.idle_sleep_seconds,
        work_sleep_min_seconds=args.work_sleep_min_seconds,
        work_sleep_max_seconds=args.work_sleep_max_seconds,
        start_signal=args.start_signal,
        max_tasks=args.max_tasks,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
