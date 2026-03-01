"""Tests for Semgrep YAML rule files — validate structure and required fields."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

_RULES_DIR = Path(__file__).parent.parent.resolve() / "data" / "semgrep_rules"

RULE_FILES = [
    "network_on_import.yaml",
    "credential_harvesting.yaml",
    "reverse_shell.yaml",
    "setup_py_exec.yaml",
]


@pytest.fixture(params=RULE_FILES)
def rule_data(request: pytest.FixtureRequest) -> tuple[str, dict]:
    """Load a Semgrep rule file and return (filename, parsed_data)."""
    path = _RULES_DIR / request.param
    assert path.exists(), f"Rule file missing: {request.param}"
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return request.param, data


class TestSemgrepRuleStructure:
    def test_has_rules_key(self, rule_data: tuple[str, dict]) -> None:
        filename, data = rule_data
        assert "rules" in data, f"{filename}: missing top-level 'rules' key"

    def test_rules_is_list(self, rule_data: tuple[str, dict]) -> None:
        filename, data = rule_data
        assert isinstance(data["rules"], list), f"{filename}: 'rules' must be a list"
        assert len(data["rules"]) >= 1, f"{filename}: must have at least 1 rule"

    def test_each_rule_has_required_fields(self, rule_data: tuple[str, dict]) -> None:
        filename, data = rule_data
        for i, rule in enumerate(data["rules"]):
            assert "id" in rule, f"{filename} rule#{i}: missing 'id'"
            assert "message" in rule, f"{filename} rule#{i}: missing 'message'"
            assert "severity" in rule, f"{filename} rule#{i}: missing 'severity'"
            assert rule["severity"] in {"ERROR", "WARNING", "INFO"}, \
                f"{filename} rule#{i}: invalid severity '{rule['severity']}'"

    def test_each_rule_has_language(self, rule_data: tuple[str, dict]) -> None:
        filename, data = rule_data
        for i, rule in enumerate(data["rules"]):
            assert "languages" in rule, f"{filename} rule#{i}: missing 'languages'"
            assert "python" in rule["languages"], \
                f"{filename} rule#{i}: expected 'python' in languages"

    def test_each_rule_has_pattern(self, rule_data: tuple[str, dict]) -> None:
        """Every rule must have at least one pattern matcher."""
        filename, data = rule_data
        pattern_keys = {"pattern", "patterns", "pattern-either", "pattern-regex"}
        for i, rule in enumerate(data["rules"]):
            has_pattern = bool(pattern_keys & set(rule.keys()))
            assert has_pattern, f"{filename} rule#{i}: no pattern key found"

    def test_rule_ids_are_unique_across_file(self, rule_data: tuple[str, dict]) -> None:
        filename, data = rule_data
        ids = [r["id"] for r in data["rules"]]
        assert len(ids) == len(set(ids)), f"{filename}: duplicate rule IDs"
