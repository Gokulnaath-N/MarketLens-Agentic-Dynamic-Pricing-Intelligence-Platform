"""Unit tests for marketlens.logging_config module."""

from __future__ import annotations

import io
import logging

from marketlens.logging_config import configure_logging, get_logger


class TestLoggingConfiguration:
    """Tests logging setup, level configuration, handler management, and emission."""

    def test_configure_logging_initializes_logger(self):
        root = configure_logging("INFO", force=True)
        assert root.level == logging.INFO
        assert len(root.handlers) >= 1

    def test_configure_logging_sets_custom_level(self):
        root = configure_logging("DEBUG", force=True)
        assert root.level == logging.DEBUG

    def test_configure_logging_idempotence_no_duplicate_handlers(self):
        # First configuration
        configure_logging("INFO", force=True)
        initial_count = len(logging.getLogger().handlers)

        # Call again without force
        configure_logging("DEBUG", force=False)
        assert len(logging.getLogger().handlers) == initial_count
        assert logging.getLogger().level == logging.DEBUG

    def test_logger_emits_message_to_stream(self):
        stream = io.StringIO()
        configure_logging("INFO", stream=stream, force=True)
        logger = get_logger("marketlens.test")

        logger.info("Test message for MarketLens AI logging.")
        output = stream.getvalue()

        assert "Test message for MarketLens AI logging." in output
        assert "INFO" in output
        assert "marketlens.test" in output

    def test_logger_respects_log_level_filtering(self):
        stream = io.StringIO()
        configure_logging("WARNING", stream=stream, force=True)
        logger = get_logger("marketlens.test_filter")

        logger.info("This info message should be filtered out.")
        logger.warning("This warning should appear.")
        output = stream.getvalue()

        assert "This info message should be filtered out." not in output
        assert "This warning should appear." in output
