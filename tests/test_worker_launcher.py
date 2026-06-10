import pytest

from computer_use_demo.api.config import ConfigError, get_settings
from computer_use_demo.api.worker_launcher import (
    LocalDockerWorkerLauncher,
    get_worker_launcher,
)


def test_worker_launcher_defaults_to_local_docker(monkeypatch):
    monkeypatch.delenv("WORKER_LAUNCHER", raising=False)

    settings = get_settings()
    launcher = get_worker_launcher()

    assert settings.worker_launcher == "local_docker"
    assert isinstance(launcher, LocalDockerWorkerLauncher)


def test_unsupported_worker_launcher_fails_clearly(monkeypatch):
    monkeypatch.setenv("WORKER_LAUNCHER", "ecs_fargate")

    with pytest.raises(ConfigError, match="Unsupported WORKER_LAUNCHER"):
        get_worker_launcher()
