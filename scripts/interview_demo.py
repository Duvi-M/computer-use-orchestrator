from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from collections import Counter
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from computer_use_demo.harness.runner import run_loop  # noqa: E402
from computer_use_demo.harness.session_harness import SessionHarness  # noqa: E402
from computer_use_demo.harness.shared_task_queue import (  # noqa: E402
    claim_next_task,
    complete_task,
    enqueue_task,
    list_tasks,
)

DEFAULT_MEMORY_FILE = Path("data") / "interview_harness_memory.json"
DEFAULT_CHECKPOINT_DIR = Path("data") / "interview_checkpoints"
DEFAULT_QUEUE_DB = Path("data") / "interview_task_queue.db"
DEFAULT_SESSION_TRACE_DIR = Path("data") / "interview_session_harness_traces"


def print_header(title: str) -> None:
    print(f"\n=== {title} ===", flush=True)  # noqa: T201


def run_command(command: Sequence[str]) -> int:
    print(f"$ {' '.join(command)}", flush=True)  # noqa: T201
    result = subprocess.run(command, cwd=REPO_ROOT, check=False)
    return result.returncode


def force_file_memory(memory_file: Path) -> None:
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ["HARNESS_MEMORY_FILE"] = str(memory_file)


def reset_path(path: Path) -> None:
    if path.is_file():
        path.unlink()
    elif path.is_dir():
        for child in sorted(path.rglob("*"), reverse=True):
            if child.is_file() or child.is_symlink():
                child.unlink()
            elif child.is_dir():
                child.rmdir()
        path.rmdir()


def command_check(_args: argparse.Namespace) -> int:
    print_header("Interview Readiness Check")
    commands = [
        [sys.executable, "-m", "ruff", "check", "computer_use_demo", "tests", "scripts", "evals"],
        [sys.executable, "-B", "-m", "pytest", "-q"],
        [sys.executable, "evals/run_eval.py", "--json"],
    ]
    for command in commands:
        code = run_command(command)
        if code != 0:
            return code
    return 0


def command_loop(args: argparse.Namespace) -> int:
    print_header("Durable Agent Loop")
    force_file_memory(args.memory_file)
    run_loop(
        goal_id=args.goal_id,
        goal_text=args.goal_text,
        checkpoint_dir=args.checkpoint_dir,
        interval_seconds=args.interval_seconds,
        max_iterations=args.max_iterations,
    )
    print(  # noqa: T201
        f"\nCheckpoint: {args.checkpoint_dir / (args.goal_id + '.json')}\n"
        f"Memory file: {args.memory_file}"
    )
    return 0


def command_memory(args: argparse.Namespace) -> int:
    print_header("Memory Recall Demo")
    force_file_memory(args.memory_file)
    if args.reset:
        reset_path(args.memory_file)
        reset_path(args.checkpoint_dir)

    print("\n# First run records one semantic memory")  # noqa: T201
    run_loop(
        goal_id="tokyo-run",
        goal_text="search Tokyo weather",
        checkpoint_dir=args.checkpoint_dir,
        interval_seconds=args.interval_seconds,
        max_iterations=args.max_iterations,
    )

    print("\n# Second run recalls related memory via shared keywords")  # noqa: T201
    run_loop(
        goal_id="osaka-run",
        goal_text="search Osaka weather",
        checkpoint_dir=args.checkpoint_dir,
        interval_seconds=args.interval_seconds,
        max_iterations=1,
    )

    if args.memory_file.exists():
        payload = json.loads(args.memory_file.read_text())
        print(  # noqa: T201
            "\nMemory summary: "
            + json.dumps(
                {
                    "path": str(args.memory_file),
                    "memories": len(payload.get("memories", [])),
                    "goal_ids": [
                        item.get("metadata", {}).get("goal_id")
                        for item in payload.get("memories", [])
                    ],
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


def command_eval(_args: argparse.Namespace) -> int:
    print_header("Offline Eval Harness")
    return run_command([sys.executable, "evals/run_eval.py", "--json"])


def command_session_harness(args: argparse.Namespace) -> int:
    print_header("Real Worker Event Adapter Demo")
    if args.reset:
        reset_path(args.trace_dir)
    harness = SessionHarness.create(
        session_id=args.session_id,
        goal_text=args.goal_text,
        trace_dir=args.trace_dir,
    )
    harness.on_worker_event("assistant_block", {"text": "I will open the browser."})
    harness.on_worker_event("tool_result", {"output": "Weather page loaded"})
    harness.on_worker_event("done", {"ok": True})
    trace_path = args.trace_dir / f"{args.session_id}.json"
    print(  # noqa: T201
        json.dumps(
            {
                "session_id": args.session_id,
                "phase": harness.state.phase,
                "observations": len(harness.state.observations),
                "evidence": len(harness.state.evidence),
                "eval_gates": [
                    {
                        "name": result.gate_name,
                        "passed": result.passed,
                    }
                    for result in harness.eval_results
                ],
                "trace_path": str(trace_path),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def command_agents(args: argparse.Namespace) -> int:
    print_header("Parallel Agents With Shared Queue")
    if args.reset:
        reset_path(args.queue_db)

    for index in range(1, args.tasks + 1):
        enqueue_task({"kind": "interview-demo", "task": index}, args.queue_db)

    def worker(agent_index: int) -> str:
        agent_id = f"agent-{agent_index}"
        while True:
            task = claim_next_task(agent_id, args.queue_db)
            if task is None:
                return agent_id
            time.sleep(args.work_seconds)
            complete_task(
                task.id,
                {
                    "agent_id": agent_id,
                    "task_id": task.id,
                    "note": "claimed under SQLite BEGIN IMMEDIATE",
                },
                args.queue_db,
            )

    with ThreadPoolExecutor(max_workers=args.agents) as executor:
        list(executor.map(worker, range(1, args.agents + 1)))

    rows = list_tasks(args.queue_db)
    completed = [row for row in rows if row["status"] == "completed"]
    distribution = Counter(row["assigned_agent"] for row in completed)
    print(  # noqa: T201
        json.dumps(
            {
                "queue_db": str(args.queue_db),
                "tasks_completed": len(completed),
                "agent_distribution": dict(sorted(distribution.items())),
                "real_tmux_command": "scripts/spawn_agents.sh 3",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def command_map(_args: argparse.Namespace) -> int:
    print_header("Vacancy Requirement Map")
    rows = [
        (
            "Spec-driven dev",
            "specs/*.md + specs/spec-kit/*",
            "Show original spec and Spec Kit version.",
        ),
        (
            "Agentic scaffolding",
            "computer_use_demo/harness/",
            "Goal, plan, action, evidence, eval, triggers.",
        ),
        (
            "Memory",
            "computer_use_demo/harness/memory.py",
            "File-backed local memory; mem0 optional.",
        ),
        (
            "Evals",
            "evals/run_eval.py",
            "Evidence + budget + gate check.",
        ),
        (
            "Runtime harness adapter",
            "computer_use_demo/harness/session_harness.py",
            "Worker events become observations, evidence, evals, and traces.",
        ),
        (
            "Parallel orchestration",
            "shared_task_queue.py + spawn_agents.sh",
            "Worktrees, tmux panes, single-writer queue.",
        ),
        (
            "Persistence",
            "runner.py + run_harness_tmux.sh",
            "Checkpoints survive terminal/SSH disconnects.",
        ),
        (
            "SaaS control plane",
            "computer_use_demo/api/",
            "FastAPI, tenancy, limits, noVNC, metrics.",
        ),
    ]
    for requirement, path, talk_track in rows:
        print(f"- {requirement}: {path} — {talk_track}")  # noqa: T201
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run interview-ready harness demos")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="Run lint, tests, and offline eval")
    check.set_defaults(func=command_check)

    loop = subparsers.add_parser("loop", help="Run bounded durable agent loop")
    loop.add_argument("--goal-id", default="interview-loop")
    loop.add_argument("--goal-text", default="search Tokyo weather")
    loop.add_argument("--checkpoint-dir", type=Path, default=DEFAULT_CHECKPOINT_DIR)
    loop.add_argument("--memory-file", type=Path, default=DEFAULT_MEMORY_FILE)
    loop.add_argument("--interval-seconds", type=float, default=0.1)
    loop.add_argument("--max-iterations", type=int, default=8)
    loop.set_defaults(func=command_loop)

    memory = subparsers.add_parser("memory", help="Show file-backed memory recall")
    memory.add_argument("--checkpoint-dir", type=Path, default=DEFAULT_CHECKPOINT_DIR)
    memory.add_argument("--memory-file", type=Path, default=DEFAULT_MEMORY_FILE)
    memory.add_argument("--interval-seconds", type=float, default=0.05)
    memory.add_argument("--max-iterations", type=int, default=8)
    memory.add_argument("--reset", action=argparse.BooleanOptionalAction, default=True)
    memory.set_defaults(func=command_memory)

    eval_parser = subparsers.add_parser("eval", help="Run offline eval harness")
    eval_parser.set_defaults(func=command_eval)

    session_harness = subparsers.add_parser(
        "session-harness",
        help="Map real worker-style events to harness state and trace",
    )
    session_harness.add_argument("--session-id", default="interview-session-harness")
    session_harness.add_argument(
        "--goal-text",
        default="Open a browser, search Tokyo weather, and report the temperature.",
    )
    session_harness.add_argument("--trace-dir", type=Path, default=DEFAULT_SESSION_TRACE_DIR)
    session_harness.add_argument("--reset", action=argparse.BooleanOptionalAction, default=True)
    session_harness.set_defaults(func=command_session_harness)

    agents = subparsers.add_parser("agents", help="Run shared queue coordination demo")
    agents.add_argument("--agents", type=int, default=5)
    agents.add_argument("--tasks", type=int, default=20)
    agents.add_argument("--queue-db", type=Path, default=DEFAULT_QUEUE_DB)
    agents.add_argument("--work-seconds", type=float, default=0.03)
    agents.add_argument("--reset", action=argparse.BooleanOptionalAction, default=True)
    agents.set_defaults(func=command_agents)

    req_map = subparsers.add_parser("map", help="Print vacancy requirement map")
    req_map.set_defaults(func=command_map)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
