from __future__ import annotations

import fcntl
import json
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Protocol

from computer_use_demo.harness.loop import Evidence, Goal

DEFAULT_MEMORY_USER_ID = "harness-demo"
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_MEMORY_PATH = Path("data") / "harness_memory.json"


@dataclass(frozen=True)
class MemoryRecord:
    text: str
    metadata: dict[str, Any]


class MemoryBackend(Protocol):
    def add(self, text: str, user_id: str, metadata: dict[str, Any]) -> Any:
        ...

    def search(self, query: str, user_id: str, limit: int = 5) -> list[Any] | dict[str, Any]:
        ...


def utc_timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def has_valid_openai_key() -> bool:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    return bool(api_key) and not api_key.startswith("sk-ant-")


def tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-zA-Z0-9]+", text.lower()) if len(token) > 2}


def evidence_signature(goal: Goal, evidence: Evidence) -> str:
    return json.dumps(
        {
            "goal_id": goal.goal_id,
            "goal_text": goal.text,
            "kind": evidence.kind,
            "summary": evidence.summary,
            "artifact_id": evidence.artifact_id,
            "confidence": evidence.confidence,
        },
        sort_keys=True,
    )


class FileBackedMemory:
    def __init__(self, path: Path = DEFAULT_MEMORY_PATH):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read_records_locked(self, handle: Any) -> list[dict[str, Any]]:
        handle.seek(0)
        raw = handle.read()
        if not raw.strip():
            return []
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(  # noqa: T201
                f"[{utc_timestamp()}] warning: corrupt memory file detected at "
                f"{self.path}; treating as empty memory ({exc})",
                flush=True,
            )
            return []
        if isinstance(payload, list):
            return payload
        return payload.get("memories", [])

    def add(self, text: str, user_id: str, metadata: dict[str, Any]) -> dict[str, Any]:
        with self.path.open("a+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                records = self._read_records_locked(handle)
                signature = metadata.get("memory_signature")
                if signature:
                    for existing in records:
                        existing_metadata = existing.get("metadata") or {}
                        if (
                            existing.get("user_id") == user_id
                            and existing_metadata.get("memory_signature") == signature
                        ):
                            return {"id": existing["id"], "deduped": True}
                record = {
                    "id": f"memory-{len(records) + 1}",
                    "user_id": user_id,
                    "text": text,
                    "memory": text,
                    "metadata": metadata,
                    "created_at": utc_timestamp(),
                }
                records.append(record)
                tmp_path = self.path.with_name(f".{self.path.name}.tmp")
                tmp_path.write_text(
                    json.dumps({"memories": records}, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                os.replace(tmp_path, self.path)
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        return {"id": record["id"]}

    def search(self, query: str, user_id: str, limit: int = 5) -> list[dict[str, Any]]:
        if limit < 1 or not self.path.exists():
            return []

        with self.path.open("r", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
            try:
                records = self._read_records_locked(handle)
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

        query_tokens = tokenize(query)
        scored = []
        for record in records:
            if record.get("user_id") != user_id:
                continue
            haystack = " ".join(
                [
                    str(record.get("text") or record.get("memory") or ""),
                    json.dumps(record.get("metadata") or {}, sort_keys=True),
                ]
            )
            score = len(query_tokens & tokenize(haystack))
            if score > 0:
                scored.append((score, record))

        scored.sort(key=lambda item: (-item[0], item[1].get("created_at", "")))
        return [record for _, record in scored[:limit]]


class Mem0Backend:
    def __init__(self, config: dict[str, Any] | None = None):
        try:
            from mem0 import Memory
        except ImportError as exc:
            raise RuntimeError(
                "mem0ai is not installed. Install computer_use_demo/requirements.txt "
                "to enable mem0 HarnessMemory."
            ) from exc

        local_config = config or {
            "embedder": {
                "provider": "huggingface",
                "config": {
                    "model": os.getenv("HARNESS_MEMORY_EMBEDDING_MODEL")
                    or DEFAULT_EMBEDDING_MODEL,
                },
            },
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "collection_name": "computer_use_harness_memory",
                    "path": "data/mem0",
                },
            },
        }
        if (
            local_config.get("embedder", {}).get("provider") == "huggingface"
            and find_spec("sentence_transformers") is None
        ):
            raise RuntimeError(
                "sentence-transformers is not installed. Install "
                "computer_use_demo/requirements.txt to enable mem0 HarnessMemory."
            )

        try:
            self.client = Memory.from_config(local_config)
        except ImportError as exc:
            raise RuntimeError(
                "HarnessMemory mem0 embedder dependencies are unavailable. Install "
                "computer_use_demo/requirements.txt to enable mem0 memory."
            ) from exc

    def add(self, text: str, user_id: str, metadata: dict[str, Any]) -> Any:
        return self.client.add(text, user_id=user_id, metadata=metadata)

    def search(self, query: str, user_id: str, limit: int = 5) -> list[Any] | dict[str, Any]:
        return self.client.search(query=query, user_id=user_id, limit=limit)


class HarnessMemory:
    def __init__(
        self,
        client: MemoryBackend | Any | None = None,
        config: dict[str, Any] | None = None,
        memory_user_id: str | None = None,
        fallback_path: Path | None = None,
    ):
        self.memory_user_id = (
            memory_user_id
            or os.getenv("HARNESS_MEMORY_USER_ID")
            or DEFAULT_MEMORY_USER_ID
        )
        self.fallback_path = fallback_path or Path(
            os.getenv("HARNESS_MEMORY_FILE") or DEFAULT_MEMORY_PATH
        )
        self.using_fallback = False
        self.fallback_reason: str | None = None
        self.backend = client or self._create_backend(config)

    def _create_backend(self, config: dict[str, Any] | None = None) -> MemoryBackend:
        if not has_valid_openai_key():
            self.using_fallback = True
            self.fallback_reason = "OPENAI_API_KEY is absent or not valid for mem0"
            return FileBackedMemory(self.fallback_path)
        try:
            return Mem0Backend(config)
        except Exception as exc:
            self.using_fallback = True
            self.fallback_reason = f"mem0 unavailable: {exc}"
            return FileBackedMemory(self.fallback_path)

    def _degrade_to_fallback(self, reason: str) -> FileBackedMemory:
        self.using_fallback = True
        self.fallback_reason = reason
        fallback = FileBackedMemory(self.fallback_path)
        self.backend = fallback
        return fallback

    def record_evidence(self, goal: Goal, evidence: Evidence) -> Any:
        text = (
            f"Goal {goal.goal_id}: {goal.text}\n"
            f"Evidence {evidence.evidence_id} ({evidence.kind}): {evidence.summary}"
        )
        metadata = {
            "goal_id": goal.goal_id,
            "goal_text": goal.text,
            "evidence_id": evidence.evidence_id,
            "evidence_kind": evidence.kind,
            "artifact_id": evidence.artifact_id,
            "confidence": evidence.confidence,
            "memory_signature": evidence_signature(goal, evidence),
        }
        try:
            return self.backend.add(text, user_id=self.memory_user_id, metadata=metadata)
        except Exception as exc:
            return self._degrade_to_fallback(f"mem0 add failed: {exc}").add(
                text,
                user_id=self.memory_user_id,
                metadata=metadata,
            )

    def recall_related(self, goal_text: str, limit: int = 5) -> list[Any]:
        if limit < 1:
            return []
        try:
            result = self.backend.search(
                query=goal_text,
                user_id=self.memory_user_id,
                limit=limit,
            )
        except Exception as exc:
            result = self._degrade_to_fallback(f"mem0 search failed: {exc}").search(
                query=goal_text,
                user_id=self.memory_user_id,
                limit=limit,
            )
        if isinstance(result, list):
            return result[:limit]
        if isinstance(result, dict):
            memories = result.get("results") or result.get("memories") or result.get("data")
            if isinstance(memories, list):
                return memories[:limit]
        return []
