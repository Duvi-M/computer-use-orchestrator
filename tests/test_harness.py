from __future__ import annotations

import pytest

from computer_use_demo.harness import (
    AgentAction,
    AgentLoopState,
    BudgetSnapshot,
    EscalationDecision,
    Evidence,
    ExecutionContract,
    Goal,
    HarnessEvent,
    Observation,
    Plan,
    RawTrace,
    SessionBudgets,
    ToolGrant,
    ToolGrantPolicy,
    TraceStore,
    TriggerDispatcher,
    evaluate_budgets,
    require_evidence,
    require_terminal_status,
)


def test_agent_loop_records_goal_to_evidence_path():
    state = AgentLoopState(goal=Goal(goal_id="g1", text="Find Tokyo weather"))
    state.set_plan(Plan(goal_id="g1", steps=("open browser", "search", "summarize")))
    state.record_action(
        AgentAction(
            action_id="a1",
            goal_id="g1",
            tool_name="browser",
            intent="search weather",
        )
    )
    state.record_observation(Observation(action_id="a1", summary="Weather page loaded"))
    state.record_evidence(
        Evidence(
            evidence_id="e1",
            goal_id="g1",
            kind="answer",
            summary="Tokyo is 22 C",
        )
    )

    assert state.phase == "evaluation"
    assert state.has_evidence("answer")
    assert require_evidence("answer").evaluate(state).passed is True
    assert require_terminal_status().evaluate(state).passed is True


def test_budget_decision_blocks_exceeded_limits():
    budgets = SessionBudgets(
        runtime_seconds=60,
        idle_seconds=30,
        max_messages=3,
        max_events=10,
        max_tokens=1000,
        max_cost_usd=0.25,
    )
    usage = BudgetSnapshot(
        runtime_seconds=61,
        idle_seconds=5,
        messages=3,
        events=2,
        tokens=999,
        cost_usd=0.01,
    )

    decision = evaluate_budgets(budgets, usage)

    assert decision.allowed is False
    assert decision.exceeded == ("runtime", "messages")
    assert "runtime" in decision.reason


def test_tool_grants_allow_and_deny_tools():
    policy = ToolGrantPolicy.local_demo_default()

    assert policy.allows(ToolGrant.BROWSER)
    assert policy.allows("desktop")
    assert not policy.allows(ToolGrant.SHELL)
    with pytest.raises(PermissionError, match="shell"):
        policy.require(ToolGrant.SHELL)


def test_trigger_dispatcher_records_and_calls_handlers():
    seen = []
    dispatcher = TriggerDispatcher()
    dispatcher.register(HarnessEvent.BUDGET_EXCEEDED, lambda event, payload: seen.append((event, payload)))

    dispatcher.emit(HarnessEvent.BUDGET_EXCEEDED, {"session_id": "s1"})

    assert dispatcher.emitted == [
        (HarnessEvent.BUDGET_EXCEEDED, {"session_id": "s1"})
    ]
    assert seen == [(HarnessEvent.BUDGET_EXCEEDED, {"session_id": "s1"})]


def test_escalation_decision_marks_loop_phase():
    state = AgentLoopState(goal=Goal(goal_id="g1", text="Recover failed worker"))

    state.record_escalation(
        EscalationDecision(
            should_escalate=True,
            reason="Worker did not become ready",
            policy="restart_worker",
            rollback_hint="Stop container and launch a fresh worker for the same session",
        )
    )

    assert state.phase == "escalation"
    assert state.escalations[0].policy == "restart_worker"


def test_execution_contract_validates_outputs_budgets_and_grants():
    contract = ExecutionContract(
        contract_id="contract-1",
        goal="Find Tokyo weather",
        required_outputs=("temperature", "source"),
        budgets=SessionBudgets(
            runtime_seconds=60,
            idle_seconds=30,
            max_messages=3,
            max_events=10,
        ),
        tool_grants=ToolGrantPolicy.local_demo_default(),
        evidence_paths=("data/traces/session-1.json",),
    )

    assert contract.validate_outputs({"temperature"}).valid is False
    assert contract.validate_outputs({"temperature", "source"}).valid is True
    assert contract.validate_budget(BudgetSnapshot(messages=1)).valid is True
    assert contract.validate_budget(BudgetSnapshot(messages=3)).valid is False
    contract.require_tool(ToolGrant.BROWSER)
    with pytest.raises(PermissionError, match="shell"):
        contract.require_tool(ToolGrant.SHELL)


def test_trace_store_persists_raw_trace(tmp_path):
    store = TraceStore(tmp_path / "traces")
    trace = RawTrace(
        session_id="session-1",
        goal="Find Tokyo weather",
        budget_usage={"messages": 1, "events": 3},
        evidence_paths=["data/artifacts/weather.png"],
    )
    trace.record_action({"tool": "browser", "intent": "search weather"})
    trace.record_observation({"summary": "Weather result visible"})
    trace.record_tool_event({"event_type": "screenshot", "event_id": "evt-1"})
    trace.finish("completed")

    path = store.write(trace)
    loaded = store.read("session-1")

    assert path.exists()
    assert loaded.final_status == "completed"
    assert loaded.actions[0]["tool"] == "browser"
    assert loaded.tool_events[0]["event_type"] == "screenshot"
