"""Tests for the typosquat detector using the expanded top_packages JSON files."""

from __future__ import annotations

from detector.layer1_metadata.typosquat_detector import analyze_typosquat


class TestTyposquatWithTopPackages:
    """Ensure typosquat detection works with the new 1000-entry top_packages."""

    def test_known_typosquat_flagged(self) -> None:
        """colourama is 1 edit from colorama — should be suspicious."""
        result = analyze_typosquat("colourama", "pypi")
        assert result["is_suspicious"] is True
        assert result["risk_score"] >= 60
        assert result["nearest_package"] is not None

    def test_exact_match_popular_package(self) -> None:
        """requests is a known top package — risk should be 0."""
        result = analyze_typosquat("requests", "pypi")
        assert result["risk_score"] == 0
        assert result["edit_distance"] == 0

    def test_npm_typosquat(self) -> None:
        """eslintt is 1 edit from eslint — should flag."""
        result = analyze_typosquat("eslintt", "npm")
        assert result["is_suspicious"] is True
        assert result["risk_score"] >= 60

    def test_npm_exact_match(self) -> None:
        """eslint is a top npm package — should not flag."""
        result = analyze_typosquat("eslint", "npm")
        assert result["risk_score"] == 0

    def test_unrelated_name_not_suspicious(self) -> None:
        """A completely unrelated name should not be suspicious."""
        result = analyze_typosquat("zzz-my-private-pkg-xyz", "pypi")
        assert result["is_suspicious"] is False

    def test_empty_package_name(self) -> None:
        result = analyze_typosquat("", "pypi")
        assert result["risk_score"] == 0
        assert result["is_suspicious"] is False

    def test_unknown_registry(self) -> None:
        result = analyze_typosquat("requests", "cargo")
        assert result["risk_score"] == 0
