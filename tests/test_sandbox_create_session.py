"""Mock tests: sandbox create writes current session."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from allox.session import get_current_session


@patch("allox.commands.sandbox.SandboxSync.create")
def test_sandbox_create_writes_session(mock_create, runner, tmp_path, monkeypatch):
    monkeypatch.setattr("allox.session.DEFAULT_SESSIONS_PATH", tmp_path / "sessions.json")

    mock_sandbox = MagicMock()
    mock_sandbox.id = "sbx-test-123"
    mock_endpoint = MagicMock()
    mock_endpoint.endpoint = "127.0.0.1:54321"
    mock_sandbox.get_endpoint.return_value = mock_endpoint
    mock_create.return_value = mock_sandbox

    result = runner(["sandbox", "create", "-o", "json", "--skip-health-check"])
    assert result.exit_code == 0, result.output

    data = json.loads(result.output)
    assert data["id"] == "sbx-test-123"
    assert data["aio_url"] == "http://127.0.0.1:54321"

    session = get_current_session(tmp_path / "sessions.json")
    assert session is not None
    assert session.sandbox_id == "sbx-test-123"
    assert session.aio_url == "http://127.0.0.1:54321"
    assert session.created_at

    mock_sandbox.close.assert_called_once()


@patch("allox.commands.sandbox.SandboxSync.create")
def test_sandbox_create_writes_session_without_aio_url(mock_create, runner, tmp_path, monkeypatch):
    monkeypatch.setattr("allox.session.DEFAULT_SESSIONS_PATH", tmp_path / "sessions.json")

    mock_sandbox = MagicMock()
    mock_sandbox.id = "sbx-no-endpoint"
    mock_sandbox.get_endpoint.side_effect = RuntimeError("endpoint unavailable")
    mock_create.return_value = mock_sandbox

    result = runner(["sandbox", "create", "-o", "json", "--skip-health-check"])
    assert result.exit_code == 0, result.output

    session = get_current_session(tmp_path / "sessions.json")
    assert session is not None
    assert session.sandbox_id == "sbx-no-endpoint"
    assert session.aio_url == ""
