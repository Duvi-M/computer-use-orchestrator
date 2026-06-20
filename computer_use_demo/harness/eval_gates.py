from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from computer_use_demo.harness.loop import AgentLoopState


@dataclass(frozen=True)
class EvalGateResult:
    passed: bool
    gate_name: str
    reason: str = ""


@dataclass(frozen=True)
class EvalGate:
    name: str
    check: Callable[[AgentLoopState], EvalGateResult]

    def evaluate(self, state: AgentLoopState) -> EvalGateResult:
        return self.check(state)


def require_evidence(kind: str | None = None) -> EvalGate:
    gate_name = f"require_evidence:{kind or 'any'}"

    def check(state: AgentLoopState) -> EvalGateResult:
        if state.has_evidence(kind):
            return EvalGateResult(passed=True, gate_name=gate_name)
        return EvalGateResult(
            passed=False,
            gate_name=gate_name,
            reason="Expected evidence was not recorded",
        )

    return EvalGate(name=gate_name, check=check)


def require_terminal_status() -> EvalGate:
    def check(state: AgentLoopState) -> EvalGateResult:
        if state.phase in {"evaluation", "next_step", "escalation"}:
            return EvalGateResult(passed=True, gate_name="require_terminal_status")
        return EvalGateResult(
            passed=False,
            gate_name="require_terminal_status",
            reason=f"Loop stopped before evaluation phase: {state.phase}",
        )

    return EvalGate(name="require_terminal_status", check=check)
