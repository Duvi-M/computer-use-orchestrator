from __future__ import annotations

import json

from computer_use_demo.harness.session_harness import SessionHarness


def test_session_harness_maps_worker_events_to_state_evidence_and_trace(tmp_path):
    harness = SessionHarness.create(
        session_id="session-harness-1",
        goal_text="Open a browser and search Tokyo weather",
        trace_dir=tmp_path,
    )

    harness.on_worker_event("assistant_block", {"text": "I will open the browser."})
    harness.on_worker_event("tool_result", {"output": "Weather page loaded"})
    harness.on_worker_event("done", {"ok": True})

    trace_path = tmp_path / "session-harness-1.json"
    trace = json.loads(trace_path.read_text())

    assert harness.state.goal.text == "Open a browser and search Tokyo weather"
    assert harness.state.observations[0].raw_event_type == "assistant_block"
    assert harness.state.evidence[0].kind == "answer"
    assert all(result.passed for result in harness.eval_results)
    assert trace["final_status"] == "completed"
    assert trace["observations"][0]["raw_event_type"] == "assistant_block"
    assert trace["budget_usage"]["eval_gates"][0]["passed"] is True
    assert trace["budget_usage"]["contract_id"] == "contract-session-harness-1"


def test_session_harness_maps_error_to_escalation_and_failed_trace(tmp_path):
    harness = SessionHarness.create(
        session_id="session-harness-error",
        goal_text="Use the desktop",
        trace_dir=tmp_path,
    )

    harness.on_worker_event("error", {"message": "worker failed"})

    trace = json.loads((tmp_path / "session-harness-error.json").read_text())

    assert harness.state.phase == "escalation"
    assert harness.state.escalations[0].should_escalate is True
    assert harness.state.escalations[0].reason == "worker failed"
    assert trace["final_status"] == "failed"
    assert trace["failure_reason"] == "worker failed"
