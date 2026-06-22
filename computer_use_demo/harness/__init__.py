"""Lightweight agentic harness primitives.

These classes document and test the orchestration concepts around the existing
Computer Use execution path. They do not replace the Claude worker loop.
"""

from computer_use_demo.harness.budgets import (
    BudgetDecision,
    BudgetSnapshot,
    SessionBudgets,
    evaluate_budgets,
)
from computer_use_demo.harness.contracts import (
    ContractValidationResult,
    ExecutionContract,
)
from computer_use_demo.harness.eval_gates import (
    EvalGate,
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
from computer_use_demo.harness.memory import HarnessMemory, MemoryRecord
from computer_use_demo.harness.session_harness import SessionHarness
from computer_use_demo.harness.tool_grants import ToolGrant, ToolGrantPolicy
from computer_use_demo.harness.traces import RawTrace, TraceStore
from computer_use_demo.harness.triggers import HarnessEvent, TriggerDispatcher

__all__ = [
    "AgentAction",
    "AgentLoopState",
    "BudgetDecision",
    "BudgetSnapshot",
    "ContractValidationResult",
    "EscalationDecision",
    "EvalGate",
    "EvalGateResult",
    "ExecutionContract",
    "Evidence",
    "Goal",
    "HarnessEvent",
    "HarnessMemory",
    "MemoryRecord",
    "Observation",
    "Plan",
    "RawTrace",
    "SessionBudgets",
    "SessionHarness",
    "ToolGrant",
    "ToolGrantPolicy",
    "TraceStore",
    "TriggerDispatcher",
    "evaluate_budgets",
    "require_evidence",
    "require_terminal_status",
]
