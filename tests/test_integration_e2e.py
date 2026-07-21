"""Optional end-to-end tests (require OpenSandbox server + Docker).

Run explicitly:
  uv run pytest -m integration tests/test_integration_e2e.py -v
"""

from __future__ import annotations

import json
import shutil
import subprocess

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def require_server(require_opensandbox_server):
    if (
        shutil.which("docker")
        and subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10,
        ).returncode
        != 0
    ):
        pytest.skip("Docker daemon not running")


def test_e2e_sandbox_lifecycle(runner, require_server, tmp_path):
    """ROADMAP 1.5: create → exec → screenshot → kill."""
    out_png = tmp_path / "test.png"
    create = runner(
        [
            "sandbox",
            "create",
            "-o",
            "json",
            "--timeout",
            "5m",
            "--env",
            "BROWSER_NO_SANDBOX",
            "--no-sandbox",
        ]
    )
    assert create.exit_code == 0, create.output
    data = json.loads(create.output)
    sandbox_id = data["id"]
    assert sandbox_id

    try:
        exec_r = runner(["aio", "exec", sandbox_id, "echo", "hello"])
        assert exec_r.exit_code == 0
        assert "hello" in exec_r.output

        failed = runner(["aio", "exec", "-o", "json", sandbox_id, "false"])
        assert failed.exit_code == 1
        assert json.loads(failed.output)["exit_code"] == 1

        timed_out = runner(
            [
                "aio",
                "exec",
                "--timeout",
                "1",
                "-o",
                "json",
                sandbox_id,
                "sleep",
                "3",
            ]
        )
        assert timed_out.exit_code == 124
        timeout_data = json.loads(timed_out.output)
        assert timeout_data["status"] == "hard_timeout"
        assert timeout_data["exit_code"] == -1

        shot = runner(["aio", "screenshot", sandbox_id, "-f", str(out_png)])
        assert shot.exit_code == 0
        assert out_png.exists() and out_png.stat().st_size > 0

        jupyter = runner(["aio", "jupyter", "run", sandbox_id, "-c", "print(2+2)", "-o", "json"])
        assert jupyter.exit_code == 0
        jdata = json.loads(jupyter.output)
        assert jdata.get("status") == "ok"

        browser = runner(["aio", "browser", "info", sandbox_id, "-o", "json"])
        assert browser.exit_code == 0
        bdata = json.loads(browser.output)
        assert bdata.get("cdp_url")
    finally:
        runner(["sandbox", "kill", sandbox_id, "-o", "json"])
