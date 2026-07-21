"""File operations via OpenSandbox execd files API."""

from __future__ import annotations

import sys

import click

from allox.context import ClientContext
from allox.utils import handle_errors, output_option, prepare_output


@click.group("file", invoke_without_command=True)
@click.pass_context
def file_group(ctx: click.Context) -> None:
    """File operations via OpenSandbox execd (ops / non-AIO path)."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@file_group.command("cat")
@click.argument("sandbox_id", required=False, default=None)
@click.argument("path")
@click.option("--encoding", default="utf-8", help="File encoding.")
@output_option("raw", "json")
@click.pass_obj
@handle_errors
def file_cat(
    obj: ClientContext,
    sandbox_id: str | None,
    path: str,
    encoding: str,
    output_format: str | None,
) -> None:
    """Read a file from the sandbox via execd."""
    prepare_output(obj, output_format, allowed=("raw", "json"), fallback="raw")
    resolved_id = obj.resolve_sandbox_id(sandbox_id)
    sandbox = obj.connect_sandbox(resolved_id)
    try:
        content = sandbox.files.read_file(path, encoding=encoding)
        if obj.output.fmt == "json":
            from allox.utils import emit_json

            emit_json({"sandbox_id": resolved_id, "path": path, "content": content})
            return
        click.echo(content, nl=False)
    finally:
        sandbox.close()


@file_group.command("write")
@click.argument("sandbox_id", required=False, default=None)
@click.argument("path")
@click.option("--content", "-c", default=None, help="Content to write. Reads stdin if omitted.")
@click.option("--encoding", default="utf-8", help="File encoding.")
@output_option("table", "json", "yaml")
@click.pass_obj
@handle_errors
def file_write(
    obj: ClientContext,
    sandbox_id: str | None,
    path: str,
    content: str | None,
    encoding: str,
    output_format: str | None,
) -> None:
    """Write content to a file in the sandbox via execd."""
    prepare_output(obj, output_format, allowed=("table", "json", "yaml", "raw"))
    resolved_id = obj.resolve_sandbox_id(sandbox_id)
    file_content = content
    if file_content is None:
        if sys.stdin.isatty():
            raise click.ClickException("Provide --content or pipe content via stdin.")
        file_content = sys.stdin.read()

    sandbox = obj.connect_sandbox(resolved_id)
    try:
        sandbox.files.write_file(path, file_content, encoding=encoding)
        obj.output.success_panel(
            {"sandbox_id": resolved_id, "path": path, "bytes": len(file_content.encode(encoding))},
            title="File Written",
        )
    finally:
        sandbox.close()
