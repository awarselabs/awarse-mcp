"""Unit tests for SeatPrune Typer CLI commands with --config and --dry-run flags."""

import os
from pathlib import Path
from typer.testing import CliRunner

from seatprune.cli import app

runner = CliRunner()


def test_scan_with_config_and_dry_run(tmp_path: Path):
    config_file = tmp_path / "test_seatprune.yaml"
    config_file.write_text(
        """
version: "1"
thresholds:
  inactive_days: 30

providers:
  github:
    org: "test-org-yaml"
    token_env: "TEST_GITHUB_TOKEN"

exemptions:
  users:
    - "exempt_yaml_user"
""",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["scan", "--config", str(config_file), "--dry-run"])
    assert result.exit_code == 0
    assert "test-org-yaml" in result.stdout
    assert "threshold=30 days" in result.stdout
    assert "(dry-run)" in result.stdout


def test_scan_with_cli_overrides(tmp_path: Path):
    config_file = tmp_path / "test_seatprune.yaml"
    config_file.write_text(
        """
version: "1"
thresholds:
  inactive_days: 60
providers:
  github:
    org: "yaml-org"
""",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["scan", "cli-override-org", "--config", str(config_file), "--threshold", "15"])
    assert result.exit_code == 0
    assert "cli-override-org" in result.stdout
    assert "threshold=15 days" in result.stdout
