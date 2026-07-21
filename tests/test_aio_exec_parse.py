"""Tests for aio exec argument parsing (flags like ls -la)."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from allox.session import Session


@patch("allox.context.ClientContext.aio_client")
def test_aio_exec_ls_dash_la_with_session(mock_aio_client, runner, monkeypatch):
    session = Session("sbx-1", "http://127.0.0.1:1", "2026-01-01T00:00:00+00:00")
    monkeypatch.setattr(
        "allox.commands.aio.get_current_session",
        lambda: session,
    )
    monkeypatch.setattr("allox.context.get_current_session", lambda: session)
    mock_client = MagicMock()
    mock_client.shell.exec_command.return_value = MagicMock(
        message="Command executed",
        data=SimpleNamespace(
            session_id="shell-1",
            status="completed",
            output="total 0\n",
            exit_code=0,
        ),
    )
    mock_aio_client.return_value = mock_client

    result = runner(["aio", "exec", "ls", "-la"])
    assert result.exit_code == 0, result.output
    mock_client.shell.exec_command.assert_called_once()
    assert mock_client.shell.exec_command.call_args.kwargs["command"] == "ls -la"
    assert mock_client.shell.exec_command.call_args.kwargs["async_mode"] is False
    assert mock_client.shell.exec_command.call_args.kwargs["hard_timeout"] == 60
    assert "timeout" not in mock_client.shell.exec_command.call_args.kwargs
    assert mock_client.shell.exec_command.call_args.kwargs["request_options"] == {
        "timeout_in_seconds": 70
    }


@patch("allox.context.ClientContext.aio_client")
def test_aio_exec_json_propagates_non_zero_exit_code(mock_aio_client, runner):
    sandbox_id = "29613df6-106f-4d3d-b194-e931171ecbe0"
    mock_client = MagicMock()
    mock_client.shell.exec_command.return_value = MagicMock(
        message="Command executed",
        data=SimpleNamespace(
            session_id="shell-2",
            status="completed",
            output="",
            exit_code=7,
        ),
    )
    mock_aio_client.return_value = mock_client

    result = runner(["aio", "exec", "-o", "json", sandbox_id, "false"])

    assert result.exit_code == 7
    assert json.loads(result.output) == {
        "session_id": "shell-2",
        "status": "completed",
        "output": "",
        "exit_code": 7,
        "message": "Command executed",
        "error": "Command exited with code 7",
    }


@patch("allox.context.ClientContext.aio_client")
def test_aio_exec_hard_timeout_returns_124(mock_aio_client, runner):
    sandbox_id = "29613df6-106f-4d3d-b194-e931171ecbe0"
    mock_client = MagicMock()
    mock_client.shell.exec_command.return_value = MagicMock(
        message="Command executed",
        data=SimpleNamespace(
            session_id="shell-3",
            status="hard_timeout",
            output="",
            exit_code=-1,
        ),
    )
    mock_aio_client.return_value = mock_client

    result = runner(["aio", "exec", "--timeout", "1", "-o", "json", sandbox_id, "sleep", "3"])

    assert result.exit_code == 124
    assert json.loads(result.output) == {
        "session_id": "shell-3",
        "status": "hard_timeout",
        "output": "",
        "exit_code": -1,
        "message": "Command executed",
        "error": "Command timed out after 1 seconds",
    }
    kwargs = mock_client.shell.exec_command.call_args.kwargs
    assert kwargs["hard_timeout"] == 1
    assert kwargs["request_options"] == {"timeout_in_seconds": 11}


@patch("allox.context.ClientContext.aio_client")
def test_aio_exec_unexpected_running_result_returns_124(mock_aio_client, runner):
    sandbox_id = "29613df6-106f-4d3d-b194-e931171ecbe0"
    mock_client = MagicMock()
    mock_client.shell.exec_command.return_value = MagicMock(
        message="Command still running",
        data=SimpleNamespace(
            session_id="shell-4",
            status="running",
            output=None,
            exit_code=None,
        ),
    )
    mock_aio_client.return_value = mock_client

    result = runner(["aio", "exec", "-o", "json", sandbox_id, "sleep", "3"])

    assert result.exit_code == 124
    payload = json.loads(result.output)
    assert payload["status"] == "running"
    assert payload["session_id"] == "shell-4"
    assert payload["error"] == "Command is still running"


@patch("allox.context.ClientContext.aio_client")
def test_aio_exec_rejects_empty_command_result(mock_aio_client, runner):
    sandbox_id = "29613df6-106f-4d3d-b194-e931171ecbe0"
    mock_client = MagicMock()
    mock_client.shell.exec_command.return_value = MagicMock(
        message="No command result",
        data=None,
    )
    mock_aio_client.return_value = mock_client

    result = runner(["aio", "exec", sandbox_id, "echo", "hello"])

    assert result.exit_code == 1
    assert "AIO shell returned no command result" in result.output


def test_aio_exec_split_args_uuid():
    from allox.utils import split_exec_args

    sid = "29613df6-106f-4d3d-b194-e931171ecbe0"
    sandbox_id, cmd = split_exec_args((sid, "ls", "-la"), has_current_session=True)
    assert sandbox_id == sid
    assert cmd == ("ls", "-la")
