from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from computer_use_demo.harness import (  # noqa: E402
    BudgetSnapshot,
    ExecutionContract,
    HarnessEvent,
    RawTrace,
    SessionBudgets,
    ToolGrantPolicy,
    TraceStore,
    TriggerDispatcher,
)


@dataclass(frozen=True)
class WorkflowResult:
    session_id: str
    contract_id: str
    status: str
    budget_allowed: bool
    trace_path: str
    elapsed_ms: int


def build_contract(index: int) -> ExecutionContract:
    return ExecutionContract(
        contract_id=f"contract-{index}",
        goal=f"Collect evidence for demo workflow {index}",
        required_outputs=("answer", "evidence"),
        budgets=SessionBudgets(
            runtime_seconds=120,
            idle_seconds=30,
            max_messages=3,
            max_events=20,
            max_tokens=2000,
            max_cost_usd=0.5,
        ),
        tool_grants=ToolGrantPolicy.local_demo_default(),
        evidence_paths=(f"data/traces/demo-workflow-{index}.json",),
        escalation_policy="ask_human",
    )


async def run_workflow(
    index: int,
    dispatcher: TriggerDispatcher,
    trace_store: TraceStore,
) -> WorkflowResult:
    started = time.monotonic()
    session_id = f"workflow-session-{index}"
    contract = build_contract(index)
    trace = RawTrace(session_id=session_id, goal=contract.goal)
    dispatcher.emit(HarnessEvent.SESSION_CREATED, {"session_id": session_id})
    trace.record_tool_event({"event_type": HarnessEvent.SESSION_CREATED.value})
    await asyncio.sleep(0.03)

    dispatcher.emit(HarnessEvent.WORKER_READY, {"session_id": session_id})
    trace.record_tool_event({"event_type": HarnessEvent.WORKER_READY.value})
    contract.require_tool("browser")
    trace.record_action({"tool": "browser", "intent": "collect evidence"})
    await asyncio.sleep(0.03)

    trace.record_observation({"summary": "Evidence collected for demo workflow"})
    produced_outputs = {"answer", "evidence"}
    output_result = contract.validate_outputs(produced_outputs)
    budget_result = contract.validate_budget(
        BudgetSnapshot(runtime_seconds=1, idle_seconds=0, messages=1, events=3)
    )
    trace.budget_usage = {
        "runtime_seconds": 1,
        "messages": 1,
        "events": 3,
        "allowed": budget_result.valid,
    }
    status = "completed" if output_result.valid and budget_result.valid else "failed"
    trace.finish(status, failure_reason=None if status == "completed" else output_result.reason)
    path = trace_store.write(trace)
    dispatcher.emit(HarnessEvent.SESSION_FINISHED, {"session_id": session_id})

    return WorkflowResult(
        session_id=session_id,
        contract_id=contract.contract_id,
        status=status,
        budget_allowed=budget_result.valid,
        trace_path=str(path),
        elapsed_ms=int((time.monotonic() - started) * 1000),
    )


async def run_demo(count: int, trace_dir: Path) -> dict[str, object]:
    dispatcher = TriggerDispatcher()
    trace_store = TraceStore(trace_dir)
    results = await asyncio.gather(
        *(run_workflow(index, dispatcher, trace_store) for index in range(1, count + 1))
    )
    return {
        "mode": "safe_parallel_workflow_simulation",
        "trace_dir": str(trace_dir),
        "results": [asdict(result) for result in results],
        "triggers": [
            {"event": event.value, "payload": payload}
            for event, payload in dispatcher.emitted
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Demonstrate parallel workflows with contracts, budgets, and traces"
    )
    parser.add_argument("--count", type=int, default=3, help="Number of workflows")
    parser.add_argument(
        "--trace-dir",
        type=Path,
        default=Path("data/traces/demo_parallel_workflows"),
        help="Directory for JSON traces",
    )
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be >= 1")

    report = asyncio.run(run_demo(args.count, args.trace_dir))
    print(json.dumps(report, indent=2, sort_keys=True))  # noqa: T201
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
