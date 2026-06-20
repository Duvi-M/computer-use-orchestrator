from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class HarnessEvent(StrEnum):
    SESSION_CREATED = "on_session_created"
    WORKER_READY = "on_worker_ready"
    BUDGET_EXCEEDED = "on_budget_exceeded"
    IDLE_TIMEOUT = "on_idle_timeout"
    AGENT_ERROR = "on_agent_error"
    EVAL_FAILED = "on_eval_failed"
    SESSION_FINISHED = "on_session_finished"


TriggerHandler = Callable[[HarnessEvent, dict[str, Any]], None]


@dataclass
class TriggerDispatcher:
    handlers: dict[HarnessEvent, list[TriggerHandler]] = field(
        default_factory=lambda: defaultdict(list)
    )
    emitted: list[tuple[HarnessEvent, dict[str, Any]]] = field(default_factory=list)

    def register(self, event: HarnessEvent | str, handler: TriggerHandler) -> None:
        self.handlers[HarnessEvent(event)].append(handler)

    def emit(self, event: HarnessEvent | str, payload: dict[str, Any] | None = None) -> None:
        harness_event = HarnessEvent(event)
        event_payload = payload or {}
        self.emitted.append((harness_event, event_payload))
        for handler in self.handlers[harness_event]:
            handler(harness_event, event_payload)
