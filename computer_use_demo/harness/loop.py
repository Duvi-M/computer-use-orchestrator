from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

LoopPhase = Literal[
    "goal",
    "plan",
    "action",
    "observation",
    "evaluation",
    "next_step",
    "escalation",
]


@dataclass(frozen=True)
class Goal:
    goal_id: str
    text: str
    success_criteria: tuple[str, ...] = ()


@dataclass(frozen=True)
class Plan:
    goal_id: str
    steps: tuple[str, ...]
    rationale: str = ""


@dataclass(frozen=True)
class AgentAction:
    action_id: str
    goal_id: str
    tool_name: str
    intent: str
    inputs: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Observation:
    action_id: str
    summary: str
    raw_event_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    goal_id: str
    kind: str
    summary: str
    artifact_id: str | None = None
    confidence: float = 1.0


@dataclass(frozen=True)
class EscalationDecision:
    should_escalate: bool
    reason: str
    policy: Literal["continue", "ask_human", "stop_session", "restart_worker", "mark_failed"]
    rollback_hint: str | None = None


@dataclass
class AgentLoopState:
    goal: Goal
    phase: LoopPhase = "goal"
    plan: Plan | None = None
    actions: list[AgentAction] = field(default_factory=list)
    observations: list[Observation] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    escalations: list[EscalationDecision] = field(default_factory=list)
    retry_count: int = 0
    current_plan_description: str = ""

    def set_plan(self, plan: Plan) -> None:
        self.plan = plan
        self.phase = "plan"

    def record_action(self, action: AgentAction) -> None:
        self.actions.append(action)
        self.phase = "action"

    def record_observation(self, observation: Observation) -> None:
        self.observations.append(observation)
        self.phase = "observation"

    def record_evidence(self, evidence: Evidence) -> None:
        self.evidence.append(evidence)
        self.phase = "evaluation"

    def record_escalation(self, decision: EscalationDecision) -> None:
        self.escalations.append(decision)
        self.phase = "escalation" if decision.should_escalate else "next_step"

    def has_evidence(self, kind: str | None = None) -> bool:
        if kind is None:
            return bool(self.evidence)
        return any(item.kind == kind for item in self.evidence)
