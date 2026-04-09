"""Tests for production-oriented Docker setup."""

import os
import time
from pathlib import Path

from bot.main import is_heartbeat_fresh, write_heartbeat


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestDockerFiles:
    def test_dockerfile_exists(self):
        dockerfile = PROJECT_ROOT / "Dockerfile"
        assert dockerfile.exists()
        assert "pip install --no-cache-dir -r requirements.txt" in dockerfile.read_text()

    def test_compose_includes_dashboard_and_bot_services(self):
        compose = (PROJECT_ROOT / "docker-compose.yml").read_text()

        assert "dashboard:" in compose
        assert "bot:" in compose
        assert "service_healthy" in compose
        assert "env_file:" in compose
        assert "http://127.0.0.1:8000/health" in compose
        assert "is_heartbeat_fresh" in compose


class TestBotHeartbeat:
    def test_write_heartbeat_creates_file(self, tmp_path):
        heartbeat_file = tmp_path / "heartbeat"

        write_heartbeat(path=heartbeat_file)

        assert heartbeat_file.exists()
        assert is_heartbeat_fresh(path=heartbeat_file, max_age_seconds=5)

    def test_is_heartbeat_fresh_returns_false_for_stale_file(self, tmp_path):
        heartbeat_file = tmp_path / "heartbeat"
        heartbeat_file.write_text("old", encoding="utf-8")
        stale_time = time.time() - 360

        os.utime(heartbeat_file, (stale_time, stale_time))

        assert not is_heartbeat_fresh(path=heartbeat_file, max_age_seconds=30)
