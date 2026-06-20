from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from computer_use_demo.harness import HarnessEvent, TriggerDispatcher  # noqa: E402


@dataclass(frozen=True)
class DemoSession:
    session_id: str
    worker_name: str
    status: str
    elapsed_ms: int


async def simulate_session(index: int, dispatcher: TriggerDispatcher) -> DemoSession:
    started = time.monotonic()
    session_id = f"demo-session-{index}"
    worker_name = f"demo-worker-{index}"
    dispatcher.emit(HarnessEvent.SESSION_CREATED, {"session_id": session_id})
    await asyncio.sleep(0.05)
    dispatcher.emit(HarnessEvent.WORKER_READY, {"session_id": session_id, "worker": worker_name})
    await asyncio.sleep(0.05)
    dispatcher.emit(HarnessEvent.SESSION_FINISHED, {"session_id": session_id})
    return DemoSession(
        session_id=session_id,
        worker_name=worker_name,
        status="completed",
        elapsed_ms=int((time.monotonic() - started) * 1000),
    )


async def run_demo(count: int) -> dict[str, object]:
    dispatcher = TriggerDispatcher()
    sessions = await asyncio.gather(
        *(simulate_session(index, dispatcher) for index in range(1, count + 1))
    )
    return {
        "mode": "safe_simulation",
        "sessions": [asdict(session) for session in sessions],
        "triggers": [
            {"event": event.value, "payload": payload}
            for event, payload in dispatcher.emitted
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Demonstrate parallel isolated session orchestration safely"
    )
    parser.add_argument("--count", type=int, default=3, help="Number of sessions to simulate")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be >= 1")

    report = asyncio.run(run_demo(args.count))
    print(json.dumps(report, indent=2, sort_keys=True))  # noqa: T201
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
