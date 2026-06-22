from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from computer_use_demo.harness.budgets import SessionBudgets
from computer_use_demo.harness.contracts import ExecutionContract
from computer_use_demo.harness.eval_gates import (
    EvalGateResult,
    require_evidence,
    require_terminal_status,
)
from computer_use_demo.harness.loop import (
    AgentAction,
    AgentLoopState,
    EscalationDecision,
    Evidence,
    Goal,
    Observation,
    Plan,
)
from computer_use_demo.harness.tool_grants import ToolGrantPolicy
from computer_use_demo.harness.traces import RawTrace, TraceStore
from computer_use_demo.harness.triggers import HarnessEvent, TriggerDispatcher

DEFAULT_SESSION_HARNESS_TRACE_DIR = Path("data") / "traces" / "session_harness"


def session_harness_trace_dir() -> Path:
    return Path(os.getenv("HARNESS_TRACE_DIR") or DEFAULT_SESSION_HARNESS_TRACE_DIR)


def _summarize_event(event_name: str, data: dict[str, Any]) -> str:
    if event_name == "assistant_block":
        text = str(data.get("text") or data.get("content") or "").strip()
        return text[:500] if text else "Assistant block received"
    if event_name == "tool_result":
        output = str(data.get("output") or data.get("text") or data.get("result") or "").strip()
        return output[:500] if output else "Tool result received"
    if event_name == "screenshot":
        return "Screenshot observation received"
    if event_name == "done":
        return "Worker completed task"
    if event_name == "error":
        return str(data.get("message") or data.get("error") or "Worker error")
    return f"Worker event received: {event_name}"


@dataclass
class SessionHarness:
    session_id: str
    goal_text: str
    contract: ExecutionContract
    state: AgentLoopState
    trace: RawTrace
    trace_store: TraceStore
    dispatcher: TriggerDispatcher = field(default_factory=TriggerDispatcher)
    eval_results: list[EvalGateResult] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        *,
        session_id: str,
        goal_text: str,
        budgets: SessionBudgets | None = None,
        trace_dir: Path | None = None,
    ) -> SessionHarness:
        goal = Goal(
            goal_id=session_id,
            text=goal_text,
            success_criteria=("answer", "evidence", "eval_gates_passed"),
        )
        contract = ExecutionContract(
            contract_id=f"contract-{session_id}",
            goal=goal_text,
            required_outputs=("answer", "evidence"),
            budgets=budgets
            or SessionBudgets(
                runtime_seconds=3600,
                idle_seconds=1800,
                max_messages=100,
                max_events=5000,
            ),
            tool_grants=ToolGrantPolicy.local_demo_default(),
            evidence_paths=(str((trace_dir or session_harness_trace_dir()) / f"{session_id}.json"),),
            escalation_policy="ask_human",
        )
        state = AgentLoopState(goal=goal)
        state.set_plan(
            Plan(
                goal_id=goal.goal_id,
                steps=(
                    "forward goal to computer-use worker",
                    "observe worker events",
                    "record evidence from completion",
                    "evaluate harness gates",
                ),
                rationale="SessionHarness adapter plan for real worker events.",
            )
        )
        trace = RawTrace(session_id=session_id, goal=goal_text)
        trace.record_action(
            {
                "action_id": "worker-message-1",
                "tool": "computer_use_worker",
                "intent": "execute user goal",
            }
        )
        harness = cls(
            session_id=session_id,
            goal_text=goal_text,
            contract=contract,
            state=state,
            trace=trace,
            trace_store=TraceStore(trace_dir or session_harness_trace_dir()),
        )
        harness.dispatcher.emit(HarnessEvent.SESSION_CREATED, {"session_id": session_id})
        harness.write_trace()
        return harness

    def on_worker_event(self, event_name: str, data: dict[str, Any]) -> None:
        self.trace.record_tool_event({"event_type": event_name, "data": data})

        if event_name in {"assistant_block", "tool_result", "screenshot", "user_message"}:
            self._record_observation(event_name, data)
        elif event_name == "done":
            self._record_evidence(event_name, data)
            self.evaluate()
            self.trace.finish("completed")
            self.dispatcher.emit(HarnessEvent.SESSION_FINISHED, {"session_id": self.session_id})
        elif event_name == "error":
            self._record_error(data)

        self.trace.budget_usage = {
            "events": len(self.trace.tool_events),
            "actions": len(self.state.actions),
            "observations": len(self.state.observations),
            "evidence": len(self.state.evidence),
        }
        self.write_trace()

    def _record_observation(self, event_name: str, data: dict[str, Any]) -> None:
        if not self.state.actions:
            self.state.record_action(
                AgentAction(
                    action_id="worker-message-1",
                    goal_id=self.state.goal.goal_id,
                    tool_name="computer_use_worker",
                    intent="execute user goal",
                )
            )
        latest_action_id = self.state.actions[-1].action_id
        observation = Observation(
            action_id=latest_action_id,
            summary=_summarize_event(event_name, data),
            raw_event_type=event_name,
            metadata={"session_id": self.session_id},
        )
        self.state.record_observation(observation)
        self.trace.record_observation(
            {
                "action_id": observation.action_id,
                "summary": observation.summary,
                "raw_event_type": observation.raw_event_type,
            }
        )

    def _record_evidence(self, event_name: str, data: dict[str, Any]) -> None:
        if self.state.evidence:
            return
        evidence = Evidence(
            evidence_id=f"evidence-{self.session_id}-1",
            goal_id=self.state.goal.goal_id,
            kind="answer",
            summary=_summarize_event(event_name, data),
            artifact_id=str(self.trace_store.trace_path(self.session_id)),
            confidence=1.0 if data.get("ok", True) else 0.5,
        )
        self.state.record_evidence(evidence)
        self.trace.evidence_paths.append(evidence.artifact_id or "")

    def _record_error(self, data: dict[str, Any]) -> None:
        reason = _summarize_event("error", data)
        self.state.record_escalation(
            EscalationDecision(
                should_escalate=True,
                reason=reason,
                policy="ask_human",
                rollback_hint="Inspect worker event stream and session trace",
            )
        )
        self.trace.finish("failed", failure_reason=reason)
        self.dispatcher.emit(
            HarnessEvent.AGENT_ERROR,
            {"session_id": self.session_id, "reason": reason},
        )

    def evaluate(self) -> list[EvalGateResult]:
        gates = [require_evidence("answer"), require_terminal_status()]
        self.eval_results = [gate.evaluate(self.state) for gate in gates]
        if not all(result.passed for result in self.eval_results):
            self.dispatcher.emit(
                HarnessEvent.EVAL_FAILED,
                {
                    "session_id": self.session_id,
                    "failed_gates": [
                        result.gate_name for result in self.eval_results if not result.passed
                    ],
                },
            )
        return self.eval_results

    def write_trace(self) -> Path:
        self.trace.budget_usage["eval_gates"] = [
            {
                "name": result.gate_name,
                "passed": result.passed,
                "reason": result.reason,
            }
            for result in self.eval_results
        ]
        self.trace.budget_usage["contract_id"] = self.contract.contract_id
        return self.trace_store.write(self.trace)
