from __future__ import annotations

from types import SimpleNamespace

import computer_use_demo.harness.memory as memory_module
from computer_use_demo.harness.loop import Evidence, Goal
from computer_use_demo.harness.memory import (
    DEFAULT_MEMORY_USER_ID,
    FileBackedMemory,
    HarnessMemory,
)


class FakeMem0Client:
    def __init__(self):
        self.add_calls = []
        self.search_calls = []

    def add(self, text, user_id=None, metadata=None):
        self.add_calls.append(
            {
                "text": text,
                "user_id": user_id,
                "metadata": metadata,
            }
        )
        return {"id": "memory-1"}

    def search(self, query, user_id=None, limit=5):
        self.search_calls.append({"query": query, "user_id": user_id, "limit": limit})
        return [{"memory": "related prior evidence"}]


class FailingMem0Client:
    def add(self, text, user_id=None, metadata=None):
        raise RuntimeError("mem0 add failed")

    def search(self, query, user_id=None, limit=5):
        raise RuntimeError("mem0 search failed")


def test_harness_memory_records_evidence_with_goal_metadata():
    client = FakeMem0Client()
    memory = HarnessMemory(client=client)
    goal = Goal(goal_id="goal-1", text="Find Tokyo weather")
    evidence = Evidence(
        evidence_id="evidence-1",
        goal_id="goal-1",
        kind="answer",
        summary="Tokyo is 22 C",
        artifact_id="artifact-1",
        confidence=0.9,
    )

    result = memory.record_evidence(goal, evidence)

    assert result == {"id": "memory-1"}
    assert client.add_calls[0]["user_id"] == DEFAULT_MEMORY_USER_ID
    assert "Tokyo is 22 C" in client.add_calls[0]["text"]
    assert client.add_calls[0]["metadata"]["goal_id"] == "goal-1"
    assert client.add_calls[0]["metadata"]["evidence_id"] == "evidence-1"
    assert client.add_calls[0]["metadata"]["artifact_id"] == "artifact-1"


def test_harness_memory_recalls_related_memories():
    client = FakeMem0Client()
    memory = HarnessMemory(client=client)

    result = memory.recall_related("weather in Tokyo", limit=3)

    assert result == [{"memory": "related prior evidence"}]
    assert client.search_calls == [
        {
            "query": "weather in Tokyo",
            "user_id": DEFAULT_MEMORY_USER_ID,
            "limit": 3,
        }
    ]


def test_harness_memory_uses_configurable_user_id_for_store_and_recall():
    client = FakeMem0Client()
    memory = HarnessMemory(client=client, memory_user_id="custom-memory-user")
    goal = Goal(goal_id="goal-2", text="Check local weather")
    evidence = Evidence(
        evidence_id="evidence-2",
        goal_id="goal-2",
        kind="answer",
        summary="Weather task completed",
    )

    memory.record_evidence(goal, evidence)
    memory.recall_related("weather", limit=1)

    assert client.add_calls[0]["user_id"] == "custom-memory-user"
    assert client.search_calls[0]["user_id"] == "custom-memory-user"


def test_harness_memory_local_config_uses_huggingface_embedder(monkeypatch):
    configs = []

    class FakeMemory:
        @staticmethod
        def from_config(config):
            configs.append(config)
            return FakeMem0Client()

    monkeypatch.setitem(__import__("sys").modules, "mem0", SimpleNamespace(Memory=FakeMemory))
    monkeypatch.setattr(memory_module, "find_spec", lambda name: object())
    monkeypatch.setenv("OPENAI_API_KEY", "sk-valid-openai-key")

    memory = HarnessMemory()

    assert isinstance(memory.backend.client, FakeMem0Client)
    assert configs[0]["embedder"]["provider"] == "huggingface"
    assert configs[0]["embedder"]["config"]["model"] == "all-MiniLM-L6-v2"
    assert configs[0]["vector_store"]["provider"] == "chroma"


def test_harness_memory_missing_sentence_transformers_fails_soft(monkeypatch):
    class FakeMemory:
        @staticmethod
        def from_config(config):
            return FakeMem0Client()

    monkeypatch.setitem(__import__("sys").modules, "mem0", SimpleNamespace(Memory=FakeMemory))
    monkeypatch.setattr(memory_module, "find_spec", lambda name: None)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-valid-openai-key")

    memory = HarnessMemory()

    assert memory.using_fallback is True
    assert isinstance(memory.backend, FileBackedMemory)


def test_harness_memory_defaults_to_file_backed_without_openai_key(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    memory = HarnessMemory(fallback_path=tmp_path / "memory.json")

    assert memory.using_fallback is True
    assert isinstance(memory.backend, FileBackedMemory)


def test_harness_memory_defaults_to_file_backed_for_anthropic_key(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-ant-not-openai")

    memory = HarnessMemory(fallback_path=tmp_path / "memory.json")

    assert memory.using_fallback is True
    assert isinstance(memory.backend, FileBackedMemory)


def test_file_backed_memory_stores_and_recalls_by_keyword(tmp_path):
    backend = FileBackedMemory(tmp_path / "memory.json")

    backend.add(
        "Goal goal-1: Find Tokyo weather\nEvidence evidence-1: Tokyo is 22 C",
        user_id=DEFAULT_MEMORY_USER_ID,
        metadata={"goal_id": "goal-1", "evidence_id": "evidence-1"},
    )

    memories = backend.search("Tokyo temperature", user_id=DEFAULT_MEMORY_USER_ID, limit=5)

    assert len(memories) == 1
    assert "Tokyo is 22 C" in memories[0]["text"]
    assert memories[0]["metadata"]["goal_id"] == "goal-1"


def test_file_backed_memory_dedupes_same_signature(tmp_path):
    backend = FileBackedMemory(tmp_path / "memory.json")
    metadata = {
        "goal_id": "goal-1",
        "evidence_id": "evidence-1",
        "memory_signature": "same-signature",
    }

    first = backend.add(
        "Goal goal-1: search Tokyo weather",
        user_id=DEFAULT_MEMORY_USER_ID,
        metadata=metadata,
    )
    second = backend.add(
        "Goal goal-1: search Tokyo weather",
        user_id=DEFAULT_MEMORY_USER_ID,
        metadata={**metadata, "evidence_id": "evidence-2"},
    )

    memories = backend.search("Tokyo weather", user_id=DEFAULT_MEMORY_USER_ID, limit=5)

    assert first["id"] == second["id"]
    assert second["deduped"] is True
    assert len(memories) == 1


def test_file_backed_memory_matches_related_weather_goal_by_shared_keywords(tmp_path):
    backend = FileBackedMemory(tmp_path / "memory.json")

    backend.add(
        "Goal tokyo-run: search Tokyo weather\n"
        "Evidence evidence-1: Tokyo weather task completed",
        user_id=DEFAULT_MEMORY_USER_ID,
        metadata={"goal_id": "tokyo-run", "goal_text": "search Tokyo weather"},
    )

    memories = backend.search("search Osaka weather", user_id=DEFAULT_MEMORY_USER_ID, limit=5)

    assert len(memories) == 1
    assert memories[0]["metadata"]["goal_id"] == "tokyo-run"


def test_harness_memory_degrades_to_file_backed_when_mem0_add_fails(tmp_path):
    memory = HarnessMemory(client=FailingMem0Client(), fallback_path=tmp_path / "memory.json")
    goal = Goal(goal_id="goal-3", text="Find Tokyo weather")
    evidence = Evidence(
        evidence_id="evidence-3",
        goal_id="goal-3",
        kind="answer",
        summary="Tokyo is warm",
    )

    memory.record_evidence(goal, evidence)
    memories = memory.recall_related("Tokyo", limit=5)

    assert memory.using_fallback is True
    assert len(memories) == 1
    assert "Tokyo is warm" in memories[0]["text"]


def test_harness_memory_degrades_to_file_backed_when_mem0_search_fails(tmp_path):
    fallback = FileBackedMemory(tmp_path / "memory.json")
    fallback.add(
        "Goal goal-4: Check Paris weather\nEvidence evidence-4: Paris is mild",
        user_id=DEFAULT_MEMORY_USER_ID,
        metadata={"goal_id": "goal-4"},
    )
    memory = HarnessMemory(client=FailingMem0Client(), fallback_path=tmp_path / "memory.json")

    memories = memory.recall_related("Paris weather", limit=5)

    assert memory.using_fallback is True
    assert len(memories) == 1
    assert "Paris is mild" in memories[0]["text"]
