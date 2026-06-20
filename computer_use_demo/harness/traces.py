from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RawTrace:
    session_id: str
    goal: str
    actions: list[dict[str, Any]] = field(default_factory=list)
    observations: list[dict[str, Any]] = field(default_factory=list)
    tool_events: list[dict[str, Any]] = field(default_factory=list)
    budget_usage: dict[str, Any] = field(default_factory=dict)
    final_status: str = "created"
    failure_reason: str | None = None
    evidence_paths: list[str] = field(default_factory=list)

    def record_action(self, action: dict[str, Any]) -> None:
        self.actions.append(action)

    def record_observation(self, observation: dict[str, Any]) -> None:
        self.observations.append(observation)

    def record_tool_event(self, event: dict[str, Any]) -> None:
        self.tool_events.append(event)

    def finish(self, status: str, *, failure_reason: str | None = None) -> None:
        self.final_status = status
        self.failure_reason = failure_reason


@dataclass(frozen=True)
class TraceStore:
    root_dir: Path

    def __post_init__(self) -> None:
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def trace_path(self, session_id: str) -> Path:
        safe_session_id = session_id.replace("/", "_")
        return self.root_dir / f"{safe_session_id}.json"

    def write(self, trace: RawTrace) -> Path:
        path = self.trace_path(trace.session_id)
        path.write_text(json.dumps(asdict(trace), indent=2, sort_keys=True))
        return path

    def read(self, session_id: str) -> RawTrace:
        data = json.loads(self.trace_path(session_id).read_text())
        return RawTrace(**data)
