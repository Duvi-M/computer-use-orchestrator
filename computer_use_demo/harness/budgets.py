from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

BudgetName = Literal[
    "runtime",
    "idle",
    "messages",
    "events",
    "tokens",
    "cost",
]


@dataclass(frozen=True)
class SessionBudgets:
    runtime_seconds: int
    idle_seconds: int
    max_messages: int
    max_events: int
    max_tokens: int | None = None
    max_cost_usd: float | None = None


@dataclass(frozen=True)
class BudgetSnapshot:
    runtime_seconds: int = 0
    idle_seconds: int = 0
    messages: int = 0
    events: int = 0
    tokens: int = 0
    cost_usd: float = 0.0


@dataclass(frozen=True)
class BudgetDecision:
    allowed: bool
    exceeded: tuple[BudgetName, ...] = ()
    reason: str = ""


def evaluate_budgets(budgets: SessionBudgets, usage: BudgetSnapshot) -> BudgetDecision:
    exceeded: list[BudgetName] = []
    if usage.runtime_seconds > budgets.runtime_seconds:
        exceeded.append("runtime")
    if usage.idle_seconds > budgets.idle_seconds:
        exceeded.append("idle")
    if usage.messages >= budgets.max_messages:
        exceeded.append("messages")
    if usage.events >= budgets.max_events:
        exceeded.append("events")
    if budgets.max_tokens is not None and usage.tokens >= budgets.max_tokens:
        exceeded.append("tokens")
    if budgets.max_cost_usd is not None and usage.cost_usd >= budgets.max_cost_usd:
        exceeded.append("cost")

    if not exceeded:
        return BudgetDecision(allowed=True)
    return BudgetDecision(
        allowed=False,
        exceeded=tuple(exceeded),
        reason="Budget exceeded: " + ", ".join(exceeded),
    )
