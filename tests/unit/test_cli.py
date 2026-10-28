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

    def test_cli_pricing_optimize_revenue(self, capsys):
        exit_code = main(
            [
                "pricing",
                "optimize",
                "--product-id",
                "uci_85123A",
                "--current-price",
                "2.95",
                "--price-min",
                "2.00",
                "--price-max",
                "4.00",
                "--step",
                "0.50",
                "--objective",
                "revenue",
            ]
        )
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "CONSTRAINED PRICING OPTIMIZATION ENGINE" in captured.out
        assert "Recommended Candidate Price" in captured.out

    def test_cli_pricing_optimize_profit_missing_cost_fails(self, capsys):
        exit_code = main(
            [
                "pricing",
                "optimize",
                "--product-id",
                "uci_85123A",
                "--current-price",
                "2.95",
                "--price-min",
                "2.00",
                "--price-max",
                "4.00",
                "--objective",
                "profit",
                # Omit --unit-cost
            ]
        )
        assert exit_code == 4
        captured = capsys.readouterr()
        assert "Pricing optimization error" in captured.err

    def test_cli_market_review(self, capsys):
        exit_code = main(
            [
                "market",
                "review",
                "--product-id",
                "uci_85123A",
                "--text",
                "Great quality and beautiful design!",
                "--method",
                "rule_based",
            ]
        )
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "CUSTOMER REVIEW INSIGHT AGENT" in captured.out
        assert "POSITIVE" in captured.out

    def test_cli_market_competitor(self, capsys):
        exit_code = main(
            [
                "market",
                "competitor",
                "--product-id",
                "uci_85123A",
                "--competitor-id",
                "rival_store",
                "--prev-price",
                "10.00",
                "--curr-price",
                "8.50",
                "--threshold",
                "5.0",
            ]
        )
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "COMPETITOR MONITORING AGENT" in captured.out
        assert "decrease" in captured.out.lower()


