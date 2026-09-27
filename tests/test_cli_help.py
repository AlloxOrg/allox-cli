from importlib import metadata

from allox_cli import __version__


def test_cli_help(runner):
    result = runner(["--help"])
    assert result.exit_code == 0
    assert "sandbox" in result.output
    assert "aio" in result.output


def test_sandbox_help(runner):
    result = runner(["sandbox", "--help"])
    assert result.exit_code == 0
    assert "create" in result.output


def test_version_matches_distribution_metadata():
    assert __version__ == metadata.version("allox-cli")
