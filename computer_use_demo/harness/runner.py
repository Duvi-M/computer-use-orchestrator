from __future__ import annotations

import argparse
import json
import os
import signal
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from computer_use_demo.harness.loop import (
    AgentAction,
    AgentLoopState,
    EscalationDecision,
    Evidence,
    Goal,
    Observation,
    Plan,
)
from computer_use_demo.harness.memory import HarnessMemory, evidence_signature

DEFAULT_CHECKPOINT_DIR = Path("data") / "checkpoints"
RUNNING = True


def utc_timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def checkpoint_path(goal_id: str, checkpoint_dir: Path = DEFAULT_CHECKPOINT_DIR) -> Path:
    safe_goal_id = goal_id.replace("/", "_")
    return checkpoint_dir / f"{safe_goal_id}.json"


def save_checkpoint(state: AgentLoopState, checkpoint_dir: Path = DEFAULT_CHECKPOINT_DIR) -> Path:
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    path = checkpoint_path(state.goal.goal_id, checkpoint_dir)
    tmp_path = path.with_name(f".{path.name}.tmp")
    payload = {
        "checkpointed_at": utc_timestamp(),
        "state": asdict(state),
    }
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    os.replace(tmp_path, path)
    return path


def _tuple(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    return tuple(value)


def state_from_dict(data: dict[str, Any]) -> AgentLoopState:
    state_data = data.get("state", data)
    goal_data = state_data["goal"]
    goal = Goal(
        goal_id=goal_data["goal_id"],
        text=goal_data["text"],
        success_criteria=_tuple(goal_data.get("success_criteria")),
    )
    plan_data = state_data.get("plan")
    plan = None
    if plan_data:
        plan = Plan(
            goal_id=plan_data["goal_id"],
            steps=_tuple(plan_data.get("steps")),
            rationale=plan_data.get("rationale", ""),
        )
    return AgentLoopState(
        goal=goal,
        phase=state_data.get("phase", "goal"),
        plan=plan,
        actions=[
            AgentAction(
                action_id=item["action_id"],
                goal_id=item["goal_id"],
                tool_name=item["tool_name"],
                intent=item["intent"],
                inputs=item.get("inputs", {}),
            )
            for item in state_data.get("actions", [])
        ],
        observations=[
            Observation(
                action_id=item["action_id"],
                summary=item["summary"],
                raw_event_type=item.get("raw_event_type"),
                metadata=item.get("metadata", {}),
            )
            for item in state_data.get("observations", [])
        ],
        evidence=[
            Evidence(
                evidence_id=item["evidence_id"],
                goal_id=item["goal_id"],
                kind=item["kind"],
                summary=item["summary"],
                artifact_id=item.get("artifact_id"),
                confidence=item.get("confidence", 1.0),
            )
            for item in state_data.get("evidence", [])
        ],
        escalations=[
            EscalationDecision(
                should_escalate=item["should_escalate"],
                reason=item["reason"],
                policy=item["policy"],
                rollback_hint=item.get("rollback_hint"),
            )
            for item in state_data.get("escalations", [])
        ],
    )


def load_checkpoint(goal_id: str, checkpoint_dir: Path = DEFAULT_CHECKPOINT_DIR) -> AgentLoopState | None:
    path = checkpoint_path(goal_id, checkpoint_dir)
    if not path.exists():
        return None
    try:
        return state_from_dict(json.loads(path.read_text()))
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        corrupted_path = path.with_name(
            f"{path.name}.corrupted-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
        )
        path.replace(corrupted_path)
        print(  # noqa: T201
            f"[{utc_timestamp()}] corrupt checkpoint detected at {path}; "
            f"moved to {corrupted_path}; starting fresh ({exc})",
            flush=True,
        )
        return None


def create_state(goal_id: str, goal_text: str) -> AgentLoopState:
    return AgentLoopState(
        goal=Goal(
            goal_id=goal_id,
            text=goal_text,
            success_criteria=("plan_created", "action_attempted", "evidence_recorded"),
        )
    )


def _format_memory(memory: Any) -> str:
    if isinstance(memory, dict):
        return str(memory.get("memory") or memory.get("text") or memory)
    return str(memory)


def memory_evidence_signature(goal: Goal, evidence: Evidence) -> str:
    return evidence_signature(goal, evidence)


def _memory_backend_label(memory: HarnessMemory) -> str:
    return "file-backed" if memory.using_fallback else "mem0"


def print_related_memories(memory: HarnessMemory | None, goal_text: str, limit: int) -> None:
    if memory is None:
        print(f"[{utc_timestamp()}] memory disabled or unavailable", flush=True)  # noqa: T201
        return

    try:
        memories = memory.recall_related(goal_text, limit=limit)
    except Exception as exc:
        print(f"[{utc_timestamp()}] memory recall failed: {exc}", flush=True)  # noqa: T201
        return
    if memory.using_fallback:
        print(f"[{utc_timestamp()}] using file-backed memory fallback", flush=True)  # noqa: T201
        fallback_reason = getattr(memory, "fallback_reason", None)
        if fallback_reason:
            print(f"[{utc_timestamp()}] memory fallback reason: {fallback_reason}", flush=True)  # noqa: T201
    print(  # noqa: T201
        f"[{utc_timestamp()}] memory recall query={goal_text!r} -> "
        f"{len(memories)} matches found",
        flush=True,
    )
    if not memories:
        return

    print(f"[{utc_timestamp()}] retrieved memories: {len(memories)}", flush=True)  # noqa: T201
    for index, item in enumerate(memories, start=1):
        print(f"[{utc_timestamp()}] memory[{index}] {_format_memory(item)}", flush=True)  # noqa: T201


def advance_state(
    state: AgentLoopState,
    *,
    memory: HarnessMemory | None = None,
    memory_recall_limit: int = 5,
    recorded_memory_signatures: set[str] | None = None,
) -> None:
    if state.phase == "goal":
        print_related_memories(memory, state.goal.text, memory_recall_limit)
        state.set_plan(
            Plan(
                goal_id=state.goal.goal_id,
                steps=(
                    "clarify goal",
                    "attempt a bounded action",
                    "record observation and evidence",
                    "evaluate next step",
                ),
                rationale="Demo harness plan generated by the long-running runner.",
            )
        )
        return

    if state.phase == "plan":
        state.record_action(
            AgentAction(
                action_id=f"action-{len(state.actions) + 1}",
                goal_id=state.goal.goal_id,
                tool_name="harness_runner",
                intent="simulate one bounded agentic attempt",
                inputs={"goal": state.goal.text},
            )
        )
        return

    if state.phase == "action":
        latest_action = state.actions[-1]
        state.record_observation(
            Observation(
                action_id=latest_action.action_id,
                summary="Simulated observation captured for checkpoint demo",
                raw_event_type="runner_tick",
                metadata={"tick": len(state.observations) + 1},
            )
        )
        return

    if state.phase == "observation":
        evidence = Evidence(
            evidence_id=f"evidence-{len(state.evidence) + 1}",
            goal_id=state.goal.goal_id,
            kind="checkpoint",
            summary="Checkpoint evidence recorded by runner",
            artifact_id=str(checkpoint_path(state.goal.goal_id)),
            confidence=1.0,
        )
        state.record_evidence(evidence)
        if memory is not None:
            signature = memory_evidence_signature(state.goal, evidence)
            if recorded_memory_signatures is None or signature not in recorded_memory_signatures:
                try:
                    memory.record_evidence(state.goal, evidence)
                    if recorded_memory_signatures is not None:
                        recorded_memory_signatures.add(signature)
                except Exception as exc:
                    print(f"[{utc_timestamp()}] memory record failed: {exc}", flush=True)  # noqa: T201
        return

    if state.phase == "evaluation":
        state.phase = "next_step"
        return

    if state.phase == "next_step":
        state.record_action(
            AgentAction(
                action_id=f"action-{len(state.actions) + 1}",
                goal_id=state.goal.goal_id,
                tool_name="harness_runner",
                intent="continue narrow retry loop after evaluation",
                inputs={"previous_evidence": len(state.evidence)},
            )
        )


def describe_state(state: AgentLoopState) -> str:
    return (
        f"phase={state.phase} "
        f"actions={len(state.actions)} "
        f"observations={len(state.observations)} "
        f"evidence={len(state.evidence)}"
    )


def handle_signal(signum: int, _frame: Any) -> None:
    global RUNNING
    RUNNING = False
    print(  # noqa: T201
        f"[{utc_timestamp()}] received signal={signum}; checkpointing before exit",
        flush=True,
    )


def run_loop(
    *,
    goal_id: str,
    goal_text: str,
    checkpoint_dir: Path,
    interval_seconds: float,
    enable_memory: bool = True,
    memory_recall_limit: int = 5,
    max_iterations: int | None = None,
) -> None:
    global RUNNING
    RUNNING = True
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    state = load_checkpoint(goal_id, checkpoint_dir)
    if state is None:
        state = create_state(goal_id, goal_text)
        print(f"[{utc_timestamp()}] starting new loop goal_id={goal_id}", flush=True)  # noqa: T201
    else:
        print(  # noqa: T201
            f"[{utc_timestamp()}] resumed checkpoint goal_id={goal_id} {describe_state(state)}",
            flush=True,
        )

    memory = None
    if enable_memory:
        memory = HarnessMemory()
        if memory.using_fallback:
            print(f"[{utc_timestamp()}] using file-backed memory fallback", flush=True)  # noqa: T201
            if memory.fallback_reason:
                print(f"[{utc_timestamp()}] memory fallback reason: {memory.fallback_reason}", flush=True)  # noqa: T201
        else:
            print(  # noqa: T201
                f"[{utc_timestamp()}] memory enabled via {_memory_backend_label(memory)}",
                flush=True,
            )

    recorded_memory_signatures: set[str] = set()
    iterations = 0
    while RUNNING and (max_iterations is None or iterations < max_iterations):
        print(f"[{utc_timestamp()}] before {describe_state(state)}", flush=True)  # noqa: T201
        advance_state(
            state,
            memory=memory,
            memory_recall_limit=memory_recall_limit,
            recorded_memory_signatures=recorded_memory_signatures,
        )
        path = save_checkpoint(state, checkpoint_dir)
        print(  # noqa: T201
            f"[{utc_timestamp()}] after  {describe_state(state)} checkpoint={path}",
            flush=True,
        )
        iterations += 1
        time.sleep(interval_seconds)

    path = save_checkpoint(state, checkpoint_dir)
    print(f"[{utc_timestamp()}] stopped {describe_state(state)} checkpoint={path}", flush=True)  # noqa: T201


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a durable demo AgentLoopState")
    parser.add_argument("--goal-id", required=True)
    parser.add_argument("--goal-text", required=True)
    parser.add_argument("--checkpoint-dir", type=Path, default=DEFAULT_CHECKPOINT_DIR)
    parser.add_argument("--interval-seconds", type=float, default=2.0)
    parser.add_argument("--disable-memory", action="store_true")
    parser.add_argument("--memory-recall-limit", type=int, default=5)
    parser.add_argument("--max-iterations", type=int)
    args = parser.parse_args()

    if not args.goal_id.strip():
        parser.error("--goal-id must not be empty")
    if not args.goal_text.strip():
        parser.error("--goal-text must not be empty")
    if args.interval_seconds <= 0:
        parser.error("--interval-seconds must be > 0")
    if args.memory_recall_limit < 1:
        parser.error("--memory-recall-limit must be >= 1")
    if args.max_iterations is not None and args.max_iterations < 1:
        parser.error("--max-iterations must be >= 1")

    run_loop(
        goal_id=args.goal_id.strip(),
        goal_text=args.goal_text.strip(),
        checkpoint_dir=args.checkpoint_dir,
        interval_seconds=args.interval_seconds,
        enable_memory=not args.disable_memory,
        memory_recall_limit=args.memory_recall_limit,
        max_iterations=args.max_iterations,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
