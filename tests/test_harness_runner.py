from __future__ import annotations

import json

import pytest

from computer_use_demo.harness.eval_gates import EvalGate, EvalGateResult
from computer_use_demo.harness.runner import (
    advance_state,
    create_state,
    evaluate_dynamic_workflow,
    load_checkpoint,
    main,
    print_related_memories,
    run_loop,
    save_checkpoint,
)


def always_failing_gate() -> EvalGate:
    return EvalGate(
        name="always_fails",
        check=lambda state: EvalGateResult(
            passed=False,
            gate_name="always_fails",
            reason=f"forced failure with {len(state.observations)} observations",
        ),
    )


def always_passing_gate() -> EvalGate:
    return EvalGate(
        name="always_passes",
        check=lambda state: EvalGateResult(passed=True, gate_name="always_passes"),
    )


def test_checkpoint_is_written_and_reloaded(tmp_path):
    checkpoint_dir = tmp_path / "checkpoints"
    state = create_state("goal-1", "Run durable harness loop")
    advance_state(state)
    advance_state(state)

    path = save_checkpoint(state, checkpoint_dir)
    loaded = load_checkpoint("goal-1", checkpoint_dir)

    assert path.exists()
    assert loaded is not None
    assert loaded.goal.goal_id == "goal-1"
    assert loaded.goal.text == "Run durable harness loop"
    assert loaded.phase == "action"
    assert loaded.plan is not None
    assert loaded.plan.steps[0] == "clarify goal"
    assert loaded.actions[0].tool_name == "harness_runner"

    payload = json.loads(path.read_text())
    assert payload["state"]["goal"]["goal_id"] == "goal-1"
    assert payload["checkpointed_at"]
    assert not list(checkpoint_dir.glob(".*.tmp"))


def test_dynamic_workflow_retries_until_max_retries_then_escalates(tmp_path, capsys):
    checkpoint_dir = tmp_path / "checkpoints"
    state = create_state("dynamic-fail", "test dynamic replanning")
    state.phase = "evaluation"

    evaluate_dynamic_workflow(
        state,
        max_retries=2,
        evaluation_gates=(always_failing_gate(),),
    )
    assert state.phase == "action"
    assert state.retry_count == 1
    assert state.plan is not None
    assert state.plan.steps[0].startswith("retry attempt 1:")

    state.phase = "evaluation"
    evaluate_dynamic_workflow(
        state,
        max_retries=2,
        evaluation_gates=(always_failing_gate(),),
    )
    assert state.phase == "action"
    assert state.retry_count == 2

    state.phase = "evaluation"
    evaluate_dynamic_workflow(
        state,
        max_retries=2,
        evaluation_gates=(always_failing_gate(),),
    )

    path = save_checkpoint(state, checkpoint_dir)
    payload = json.loads(path.read_text())
    output = capsys.readouterr().out

    assert state.phase == "escalation"
    assert state.retry_count == 2
    assert state.escalations[-1].reason == "max retries exceeded"
    assert payload["state"]["retry_count"] == 2
    assert payload["state"]["current_plan_description"] == "max retries exceeded -> escalating"
    assert "eval gate failed:" in output
    assert "max retries exceeded -> escalating" in output


def test_dynamic_workflow_continues_when_gate_passes(capsys):
    state = create_state("dynamic-pass", "test dynamic pass")
    state.phase = "evaluation"

    evaluate_dynamic_workflow(
        state,
        max_retries=2,
        evaluation_gates=(always_passing_gate(),),
    )

    output = capsys.readouterr().out

    assert state.phase == "next_step"
    assert state.retry_count == 0
    assert state.current_plan_description == "eval gate passed -> continuing"
    assert "eval gate passed -> continuing" in output


def test_corrupt_checkpoint_is_moved_aside_and_starts_fresh(tmp_path, capsys):
    checkpoint_dir = tmp_path / "checkpoints"
    checkpoint_dir.mkdir()
    checkpoint = checkpoint_dir / "goal-corrupt.json"
    checkpoint.write_text("{not valid json", encoding="utf-8")

    loaded = load_checkpoint("goal-corrupt", checkpoint_dir)

    output = capsys.readouterr().out
    corrupted_files = list(checkpoint_dir.glob("goal-corrupt.json.corrupted-*"))

    assert loaded is None
    assert "corrupt checkpoint detected" in output
    assert "starting fresh" in output
    assert not checkpoint.exists()
    assert len(corrupted_files) == 1


def test_runner_cli_rejects_empty_goal_id(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "runner",
            "--goal-id",
            "   ",
            "--goal-text",
            "search Tokyo weather",
            "--max-iterations",
            "1",
        ],
    )

    with pytest.raises(SystemExit):
        main()


def test_runner_cli_rejects_empty_goal_text(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "runner",
            "--goal-id",
            "goal-1",
            "--goal-text",
            "   ",
            "--max-iterations",
            "1",
        ],
    )

    with pytest.raises(SystemExit):
        main()


class FakeFallbackMemory:
    using_fallback = True

    def recall_related(self, goal_text, limit=5):
        return [{"memory": f"remembered {goal_text}", "text": "stored memory"}]

    def record_evidence(self, goal, evidence):
        raise RuntimeError("memory write failed")


def test_runner_prints_file_backed_memory_fallback(capsys):
    print_related_memories(FakeFallbackMemory(), "Tokyo weather", 5)

    output = capsys.readouterr().out
    assert "using file-backed memory fallback" in output
    assert "retrieved memories:" in output


def test_runner_does_not_crash_when_memory_record_fails():
    state = create_state("goal-2", "Run durable harness loop")
    advance_state(state)
    advance_state(state)
    advance_state(state)

    advance_state(state, memory=FakeFallbackMemory())

    assert state.phase == "evaluation"
    assert len(state.evidence) == 1


def test_runner_dedupes_memory_records_while_checkpointing(monkeypatch, tmp_path):
    memory_path = tmp_path / "harness_memory.json"
    checkpoint_dir = tmp_path / "checkpoints"
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("HARNESS_MEMORY_FILE", str(memory_path))

    run_loop(
        goal_id="tokyo-run",
        goal_text="search Tokyo weather",
        checkpoint_dir=checkpoint_dir,
        interval_seconds=0.001,
        max_iterations=12,
    )

    payload = json.loads(memory_path.read_text())
    memories = payload["memories"]

    assert len(memories) == 1
    assert memories[0]["metadata"]["goal_id"] == "tokyo-run"
    assert (checkpoint_dir / "tokyo-run.json").exists()


def test_runner_recreates_memory_when_checkpoint_exists_but_memory_file_is_missing(
    monkeypatch,
    tmp_path,
):
    memory_path = tmp_path / "harness_memory.json"
    checkpoint_dir = tmp_path / "checkpoints"
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("HARNESS_MEMORY_FILE", str(memory_path))

    run_loop(
        goal_id="osaka-run",
        goal_text="search Osaka weather",
        checkpoint_dir=checkpoint_dir,
        interval_seconds=0.001,
        max_iterations=4,
    )
    memory_path.unlink()

    run_loop(
        goal_id="osaka-run",
        goal_text="search Osaka weather",
        checkpoint_dir=checkpoint_dir,
        interval_seconds=0.001,
        max_iterations=4,
    )

    payload = json.loads(memory_path.read_text())

    assert len(payload["memories"]) == 1
    assert payload["memories"][0]["metadata"]["goal_id"] == "osaka-run"


def test_runner_recalls_related_file_backed_memory_end_to_end(monkeypatch, tmp_path, capsys):
    memory_path = tmp_path / "harness_memory.json"
    checkpoint_dir = tmp_path / "checkpoints"
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("HARNESS_MEMORY_FILE", str(memory_path))

    run_loop(
        goal_id="tokyo-run",
        goal_text="search Tokyo weather",
        checkpoint_dir=checkpoint_dir,
        interval_seconds=0.001,
        max_iterations=4,
    )
    capsys.readouterr()

    run_loop(
        goal_id="osaka-run",
        goal_text="search Osaka weather",
        checkpoint_dir=checkpoint_dir,
        interval_seconds=0.001,
        max_iterations=1,
    )

    output = capsys.readouterr().out
    assert "memory recall query='search Osaka weather' -> 1 matches found" in output
    assert "tokyo-run" in output
