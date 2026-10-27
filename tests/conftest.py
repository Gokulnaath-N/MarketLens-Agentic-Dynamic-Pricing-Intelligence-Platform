"""Pytest test suite configuration and shared fixtures for MarketLens AI."""

from __future__ import annotations

import logging
from pathlib import Path
import pytest


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for generating isolated test YAML configs."""
    config_dir = tmp_path / "configs"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


@pytest.fixture(autouse=True)
def reset_logging():
    """Ensure logging handlers are cleaned up between tests to prevent test bleed."""
    yield
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        handler.close()
