"""Unit tests for MarketLens AI CLI commands."""

from __future__ import annotations

import pytest
from marketlens.cli import main


class TestCLICommands:
    """Tests CLI entry points without making network requests."""

    def test_cli_help(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "MarketLens AI" in captured.out

    def test_cli_datasets_discover(self, capsys):
        exit_code = main(["datasets", "discover"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "DATASET CANDIDATE DISCOVERY" in captured.out
        assert "uci_online_retail_ii" in captured.out

    def test_cli_datasets_status(self, capsys):
        exit_code = main(["datasets", "status"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "LOCAL DATASET ACQUISITION STATUS" in captured.out

    def test_cli_datasets_download_dry_run(self, capsys):
        exit_code = main(["datasets", "download", "--source", "uci_online_retail_ii", "--dry-run"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "[DRY RUN PLAN COMPLETED]" in captured.out

    def test_cli_datasets_download_unknown_source_fails(self, capsys):
        exit_code = main(["datasets", "download", "--source", "non_existent_source"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Unknown dataset source" in captured.err

    def test_cli_datasets_download_blocked_source_fails(self, capsys):
        exit_code = main(["datasets", "download", "--source", "olist_brazilian_ecommerce"])
        assert exit_code == 2
        captured = capsys.readouterr()
        assert "Cannot acquire dataset" in captured.err
