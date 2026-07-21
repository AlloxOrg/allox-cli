"""Config resolution tests."""

from __future__ import annotations

from allox.config import resolve_config


def test_skip_health_check_from_config(tmp_path):
    cfg = tmp_path / "config.toml"
    cfg.write_text(
        """
[defaults]
skip_health_check = true
image = "opensandbox/code-interpreter:latest"
""",
        encoding="utf-8",
    )
    resolved = resolve_config(config_path=cfg)
    assert resolved["skip_health_check"] is True
    assert resolved["default_image"] == "opensandbox/code-interpreter:latest"


def test_skip_health_check_default_false(tmp_path):
    cfg = tmp_path / "config.toml"
    cfg.write_text('[connection]\ndomain = "localhost:8080"\n', encoding="utf-8")
    resolved = resolve_config(config_path=cfg)
    assert resolved["skip_health_check"] is False
