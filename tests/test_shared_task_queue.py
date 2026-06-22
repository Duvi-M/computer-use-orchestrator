from __future__ import annotations

import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

import computer_use_demo.harness.shared_task_queue as queue_module
from computer_use_demo.harness.shared_task_queue import (
    claim_next_task,
    complete_task,
    enqueue_task,
    list_tasks,
)


def test_concurrent_claims_do_not_double_assign(tmp_path):
    db_path = tmp_path / "task_queue.db"
    task_ids = [enqueue_task({"task": index}, db_path) for index in range(10)]

    def claim(agent_index: int):
        return claim_next_task(f"agent-{agent_index}", db_path)

    with ThreadPoolExecutor(max_workers=5) as executor:
        claimed = list(executor.map(claim, range(5)))

    claimed_ids = [task.id for task in claimed if task is not None]

    assert len(claimed_ids) == 5
    assert len(set(claimed_ids)) == len(claimed_ids)
    assert set(claimed_ids).issubset(set(task_ids))

    tasks = list_tasks(db_path)
    claimed_rows = [task for task in tasks if task["status"] == "claimed"]
    assert len(claimed_rows) == 5
    assert len({task["assigned_agent"] for task in claimed_rows}) == 5


def test_concurrent_workers_complete_tasks_across_multiple_agents(tmp_path):
    db_path = tmp_path / "task_queue.db"
    for index in range(18):
        enqueue_task({"task": index}, db_path)

    def work(agent_index: int) -> str:
        agent_id = f"agent-{agent_index}"
        while True:
            task = claim_next_task(agent_id, db_path)
            if task is None:
                return agent_id
            time.sleep(0.02)
            complete_task(task.id, {"agent_id": agent_id}, db_path)

    with ThreadPoolExecutor(max_workers=5) as executor:
        list(executor.map(work, range(5)))

    tasks = list_tasks(db_path)
    completed_rows = [task for task in tasks if task["status"] == "completed"]
    completed_agents = {task["assigned_agent"] for task in completed_rows}

    assert len(completed_rows) == 18
    assert len(completed_agents) >= 3


def test_claim_next_task_reports_locked_database_clearly(monkeypatch, tmp_path):
    class LockedConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def execute(self, _sql):
            raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(queue_module, "init_queue", lambda _db_path: None)
    monkeypatch.setattr(queue_module, "connect", lambda _db_path: LockedConnection())

    with pytest.raises(RuntimeError, match="task queue busy .*agent_id=agent-locked"):
        claim_next_task("agent-locked", tmp_path / "task_queue.db")
