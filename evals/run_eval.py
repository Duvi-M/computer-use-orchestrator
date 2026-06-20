from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from computer_use_demo.harness import (  # noqa: E402
    AgentAction,
    AgentLoopState,
    BudgetSnapshot,
    Evidence,
    Goal,
    HarnessEvent,
    Observation,
    Plan,
    SessionBudgets,
    ToolGrant,
    ToolGrantPolicy,
    TriggerDispatcher,
    evaluate_budgets,
    require_evidence,
    require_terminal_status,
)

SCENARIO_PATH = Path(__file__).parent / "scenarios" / "session_lifecycle.json"


def load_scenario(path: Path = SCENARIO_PATH) -> dict[str, Any]:
    return json.loads(path.read_text())


def run_offline_eval(scenario: dict[str, Any]) -> dict[str, Any]:
    dispatcher = TriggerDispatcher()
    emitted: list[str] = []
    for event in HarnessEvent:
        dispatcher.register(event, lambda event, payload: emitted.append(event.value))

    budgets = SessionBudgets(**scenario["budgets"])
    usage = BudgetSnapshot(runtime_seconds=20, idle_seconds=1, messages=1, events=5, tokens=400)
    budget_decision = evaluate_budgets(budgets, usage)

    grants = ToolGrantPolicy(allowed=frozenset(ToolGrant(item) for item in scenario["tool_grants"]))
    grants.require(ToolGrant.BROWSER)
    grants.require(ToolGrant.DESKTOP)

    goal = Goal(
        goal_id="eval-goal-1",
        text=scenario["goal"],
        success_criteria=tuple(scenario["success_criteria"]),
    )
    state = AgentLoopState(goal=goal)
    dispatcher.emit(HarnessEvent.SESSION_CREATED, {"session_id": "eval-session-1"})
    dispatcher.emit(HarnessEvent.WORKER_READY, {"session_id": "eval-session-1"})
    state.set_plan(
        Plan(
            goal_id=goal.goal_id,
            steps=("open browser", "search weather", "extract temperature"),
        )
    )
    state.record_action(
        AgentAction(
            action_id="action-1",
            goal_id=goal.goal_id,
            tool_name="browser",
            intent="search current weather in Tokyo",
        )
    )
    state.record_observation(
        Observation(
            action_id="action-1",
            summary="Weather result page is visible",
            raw_event_type="screenshot",
        )
    )
    state.record_evidence(
        Evidence(
            evidence_id="evidence-1",
            goal_id=goal.goal_id,
            kind="answer",
            summary="Temperature evidence was recorded for Tokyo weather",
            confidence=0.9,
        )
    )
    dispatcher.emit(HarnessEvent.SESSION_FINISHED, {"session_id": "eval-session-1"})

    gates = [require_evidence("answer"), require_terminal_status()]
    gate_results = [gate.evaluate(state) for gate in gates]
    passed = budget_decision.allowed and all(result.passed for result in gate_results)
    if not passed:
        dispatcher.emit(HarnessEvent.EVAL_FAILED, {"scenario": scenario["name"]})

    return {
        "scenario": scenario["name"],
        "passed": passed,
        "budget": {
            "allowed": budget_decision.allowed,
            "exceeded": list(budget_decision.exceeded),
            "reason": budget_decision.reason,
        },
        "gates": [
            {
                "name": result.gate_name,
                "passed": result.passed,
                "reason": result.reason,
            }
            for result in gate_results
        ],
        "triggers": emitted,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run offline harness eval scenarios")
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    args = parser.parse_args()

    report = run_offline_eval(load_scenario())
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))  # noqa: T201
    else:
        status = "PASS" if report["passed"] else "FAIL"
        print(f"{status} {report['scenario']}")  # noqa: T201
        for gate in report["gates"]:
            print(f"- {gate['name']}: {'pass' if gate['passed'] else 'fail'}")  # noqa: T201
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
