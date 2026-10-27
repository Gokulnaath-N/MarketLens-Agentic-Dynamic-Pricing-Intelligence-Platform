"""Unit tests for marketlens.config module."""

from __future__ import annotations

import os
from pathlib import Path
import pytest

from marketlens.config import (
    ConfigurationError,
    get_configs_dir,
    get_env_var,
    get_project_root,
    load_yaml_config,
)


class TestConfigResolution:
    """Tests project directory and root resolution."""

    def test_get_project_root_exists(self):
        root = get_project_root()
        assert root.exists()
        assert (root / "MARKETLENS_AI_KNOWLEDGE_BASE.md").exists()
        assert (root / "src" / "marketlens").exists()

    def test_get_configs_dir_exists(self):
        configs_dir = get_configs_dir()
        assert configs_dir.exists()
        assert (configs_dir / "app.yaml").exists()


class TestYamlConfigLoading:
    """Tests loading, parsing, and error-handling of YAML configuration files."""

    def test_load_valid_yaml(self, temp_config_dir: Path):
        sample_file = temp_config_dir / "valid.yaml"
        sample_file.write_text("model:\n  name: xgboost\n  learning_rate: 0.05\n", encoding="utf-8")

        config = load_yaml_config("valid.yaml", configs_dir=temp_config_dir)
        assert isinstance(config, dict)
        assert config["model"]["name"] == "xgboost"
        assert config["model"]["learning_rate"] == 0.05

    def test_load_empty_yaml_allowed(self, temp_config_dir: Path):
        empty_file = temp_config_dir / "empty.yaml"
        empty_file.write_text("", encoding="utf-8")

        config = load_yaml_config("empty.yaml", configs_dir=temp_config_dir, allow_empty=True)
        assert config == {}

    def test_load_empty_yaml_disallowed(self, temp_config_dir: Path):
        empty_file = temp_config_dir / "empty.yaml"
        empty_file.write_text("", encoding="utf-8")

        with pytest.raises(ConfigurationError, match="is empty"):
            load_yaml_config("empty.yaml", configs_dir=temp_config_dir, allow_empty=False)

    def test_load_missing_file_raises_filenotfound(self, temp_config_dir: Path):
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            load_yaml_config("nonexistent.yaml", configs_dir=temp_config_dir)

    def test_load_malformed_yaml_raises_configuration_error(self, temp_config_dir: Path):
        malformed = temp_config_dir / "malformed.yaml"
        malformed.write_text("key: [unclosed list", encoding="utf-8")

        with pytest.raises(ConfigurationError, match="Failed to parse YAML file"):
            load_yaml_config("malformed.yaml", configs_dir=temp_config_dir)

    def test_load_non_dict_yaml_raises_configuration_error(self, temp_config_dir: Path):
        non_dict = temp_config_dir / "list.yaml"
        non_dict.write_text("- item1\n- item2\n", encoding="utf-8")

        with pytest.raises(ConfigurationError, match="Expected top-level dictionary"):
            load_yaml_config("list.yaml", configs_dir=temp_config_dir)

    def test_load_with_relative_filename_defaults_to_project_configs(self):
        config = load_yaml_config("app.yaml")
        assert isinstance(config, dict)
        assert "app" in config
        assert config["app"]["name"] == "MarketLens AI"

    def test_load_all_standard_configs(self):
        """Verify that all five required configuration files load successfully."""
        configs_to_test = [
            "app.yaml",
            "datasets.yaml",
            "forecasting.yaml",
            "pricing.yaml",
            "agents.yaml",
        ]
        for config_name in configs_to_test:
            cfg = load_yaml_config(config_name)
            assert isinstance(cfg, dict), f"Failed to load {config_name} as dictionary"
            assert len(cfg) > 0, f"Expected non-empty config in {config_name}"


class TestEnvVarHelper:
    """Tests environment variable extraction."""

    def test_get_env_var_present(self, monkeypatch):
        monkeypatch.setenv("TEST_KEY", "test_value")
        assert get_env_var("TEST_KEY") == "test_value"

    def test_get_env_var_default(self):
        assert get_env_var("NON_EXISTENT_VAR_12345", default="fallback") == "fallback"

    def test_get_env_var_required_missing_raises(self, monkeypatch):
        monkeypatch.delenv("MISSING_REQUIRED_KEY", raising=False)
        with pytest.raises(ConfigurationError, match="Required environment variable"):
            get_env_var("MISSING_REQUIRED_KEY", required=True)
