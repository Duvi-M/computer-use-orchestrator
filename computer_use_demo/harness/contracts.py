from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from computer_use_demo.harness.budgets import (
    BudgetDecision,
    BudgetSnapshot,
    SessionBudgets,
    evaluate_budgets,
)
from computer_use_demo.harness.tool_grants import ToolGrant, ToolGrantPolicy

CompletionCondition = Literal["evidence_recorded", "eval_gates_passed", "human_approved"]


@dataclass(frozen=True)
class ContractValidationResult:
    valid: bool
    reason: str = ""
    budget_decision: BudgetDecision | None = None


@dataclass(frozen=True)
class ExecutionContract:
    contract_id: str
    goal: str
    required_outputs: tuple[str, ...]
    budgets: SessionBudgets
    tool_grants: ToolGrantPolicy
    completion_conditions: tuple[CompletionCondition, ...] = (
        "evidence_recorded",
        "eval_gates_passed",
    )
    evidence_paths: tuple[str, ...] = ()
    escalation_policy: Literal[
        "ask_human",
        "stop_session",
        "restart_worker",
        "mark_failed",
    ] = "ask_human"

    def require_tool(self, grant: ToolGrant | str) -> None:
        self.tool_grants.require(grant)

    def validate_budget(self, usage: BudgetSnapshot) -> ContractValidationResult:
        decision = evaluate_budgets(self.budgets, usage)
        return ContractValidationResult(
            valid=decision.allowed,
            reason=decision.reason,
            budget_decision=decision,
        )

    def validate_outputs(self, produced_outputs: set[str]) -> ContractValidationResult:
        missing = [item for item in self.required_outputs if item not in produced_outputs]
        if missing:
            return ContractValidationResult(
                valid=False,
                reason="Missing required outputs: " + ", ".join(missing),
            )
        return ContractValidationResult(valid=True)
