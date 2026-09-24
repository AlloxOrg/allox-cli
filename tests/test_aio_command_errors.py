"""Unit tests for AIO command error and empty-response handling."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch


SANDBOX_ID = "29613df6-106f-4d3d-b194-e931171ecbe0"


@patch("allox.context.ClientContext.aio_client")
def test_aio_exec_reports_empty_response_message(mock_aio_client, runner):
    client = MagicMock()
    client.shell.exec_command.return_value = SimpleNamespace(
        data=None,
        message="shell unavailable",
    )
    mock_aio_client.return_value = client

    result = runner(["aio", "exec", SANDBOX_ID, "echo", "hello"])

    assert result.exit_code == 1
    assert "Error: shell unavailable" in result.output


@patch("allox.context.ClientContext.aio_client")
def test_aio_read_reports_default_message_for_empty_response(mock_aio_client, runner):
    client = MagicMock()
    client.file.read_file.return_value = SimpleNamespace(data=None, message=None)
    mock_aio_client.return_value = client

    result = runner(["aio", "read", SANDBOX_ID, "/workspace/example.txt"])

    assert result.exit_code == 1
    assert "Error: File read returned no data" in result.output


@patch("allox.context.ClientContext.aio_client")
def test_aio_jupyter_reports_empty_response_message(mock_aio_client, runner):
    client = MagicMock()
    client.jupyter.execute_code.return_value = SimpleNamespace(
        data=None,
        message="kernel unavailable",
    )
    mock_aio_client.return_value = client

    result = runner(["aio", "jupyter", "run", SANDBOX_ID, "-c", "print(1)"])

    assert result.exit_code == 1
    assert "Error: kernel unavailable" in result.output


@patch("allox.context.ClientContext.aio_client")
def test_aio_browser_info_reports_default_message_for_empty_response(
    mock_aio_client,
    runner,
):
    client = MagicMock()
    client.browser.get_info.return_value = SimpleNamespace(data=None, message=None)
    mock_aio_client.return_value = client

    result = runner(["aio", "browser", "info", SANDBOX_ID])

    assert result.exit_code == 1
    assert "Error: Browser info returned no data" in result.output


@patch("allox.commands.aio.parse_mcp_target")
@patch("allox.context.ClientContext.aio_client")
def test_aio_mcp_call_rejects_missing_tool_after_parsing(
    mock_aio_client,
    mock_parse_mcp_target,
    runner,
):
    mock_parse_mcp_target.return_value = (SANDBOX_ID, "browser", None)

    result = runner(["aio", "mcp", "call", "browser", "navigate"])

    assert result.exit_code == 1
    assert "Error: Missing MCP tool name" in result.output
    mock_aio_client.return_value.mcp.execute_mcp_tool.assert_not_called()
