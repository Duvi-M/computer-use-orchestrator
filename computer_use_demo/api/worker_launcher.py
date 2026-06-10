from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Protocol

import httpx

from computer_use_demo.api.config import ConfigError, get_settings
from computer_use_demo.api.worker_manager import (
    WorkerInfo,
    cleanup_project_workers,
    start_worker,
    stop_worker,
)

logger = logging.getLogger(__name__)


class WorkerReadyError(RuntimeError):
    pass


class WorkerLauncher(Protocol):
    def create_worker(self, *, session_id: str, api_key: str) -> WorkerInfo:
        pass

    async def wait_until_ready(self, worker: WorkerInfo) -> None:
        pass

    async def get_worker_status(self, worker: WorkerInfo) -> dict[str, Any]:
        pass

    def stop_worker(self, worker: WorkerInfo) -> None:
        pass

    def cleanup_orphans(self) -> int:
        pass

    def get_worker_events_url(self, worker: WorkerInfo) -> str:
        pass

    def get_worker_message_url(self, worker: WorkerInfo) -> str:
        pass

    def get_worker_ui_metadata(self, worker: WorkerInfo) -> dict[str, Any]:
        pass


class LocalDockerWorkerLauncher:
    def create_worker(self, *, session_id: str, api_key: str) -> WorkerInfo:
        return start_worker(session_id=session_id, api_key=api_key)

    async def wait_until_ready(self, worker: WorkerInfo) -> None:
        settings = get_settings()
        url = f"http://{worker.host}:{worker.http}/health"
        deadline = time.time() + settings.worker_ready_timeout_seconds
        last_error = "no response yet"
        logger.info(
            "worker_readiness_check_start worker=%s host=%s http_port=%s novnc_port=%s timeout_seconds=%s",
            worker.name,
            worker.host,
            worker.http,
            worker.novnc,
            settings.worker_ready_timeout_seconds,
        )

        async with httpx.AsyncClient(timeout=2.0) as client:
            while time.time() < deadline:
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        logger.info(
                            "worker_readiness_check_ok worker=%s host=%s http_port=%s",
                            worker.name,
                            worker.host,
                            worker.http,
                        )
                        return
                    last_error = f"health returned HTTP {response.status_code}"
                except Exception as exc:
                    last_error = f"{type(exc).__name__}: {exc}"
                await asyncio.sleep(settings.worker_ready_poll_seconds)

        message = (
            "Worker did not become ready in time "
            f"name={worker.name} host={worker.host} http={worker.http} "
            f"novnc={worker.novnc} timeout={settings.worker_ready_timeout_seconds}s "
            f"last_error={last_error}"
        )
        logger.error(message)
        raise WorkerReadyError(message)

    async def get_worker_status(self, worker: WorkerInfo) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"http://{worker.host}:{worker.http}/status")
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, dict) else {"busy": False, "status": "unknown"}

    def stop_worker(self, worker: WorkerInfo) -> None:
        stop_worker(worker.name)

    def cleanup_orphans(self) -> int:
        return cleanup_project_workers()

    def get_worker_events_url(self, worker: WorkerInfo) -> str:
        return f"http://{worker.host}:{worker.http}/events"

    def get_worker_message_url(self, worker: WorkerInfo) -> str:
        return f"http://{worker.host}:{worker.http}/messages"

    def get_worker_ui_metadata(self, worker: WorkerInfo) -> dict[str, Any]:
        settings = get_settings()
        novnc_url = (
            f"http://{settings.public_host}:{worker.novnc}/vnc.html"
            "?resize=scale&autoconnect=1&view_only=1&reconnect=1&reconnect_delay=2000"
        )
        return {
            "novnc_url": novnc_url,
            "vnc_port": worker.vnc,
            "novnc_port": worker.novnc,
            "streamlit_port": worker.streamlit,
            "http_port": worker.http,
        }

def get_worker_launcher() -> WorkerLauncher:
    launcher = get_settings().worker_launcher
    if launcher == "local_docker":
        return LocalDockerWorkerLauncher()
    raise ConfigError(
        "Unsupported WORKER_LAUNCHER "
        f"{launcher!r}; supported values: local_docker"
    )
