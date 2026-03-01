"""Tests for data layer scripts — dataset generation, top packages, and Semgrep rules."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).parent.parent.resolve()
_TOP_PACKAGES_DIR = _PROJECT_ROOT / "data" / "top_packages"
_SEMGREP_RULES_DIR = _PROJECT_ROOT / "data" / "semgrep_rules"


class TestDownloadBackstabbers:
    def test_produces_valid_json(self, tmp_path: Path) -> None:
        from data.datasets.download_backstabbers import download_backstabbers_dataset

        records = download_backstabbers_dataset(output_dir=str(tmp_path), force=True)
        assert isinstance(records, list)
        assert len(records) >= 25  # we added ~30 unique packages

    def test_records_have_required_fields(self, tmp_path: Path) -> None:
        from data.datasets.download_backstabbers import download_backstabbers_dataset

        records = download_backstabbers_dataset(output_dir=str(tmp_path), force=True)
        for rec in records:
            assert "package_name" in rec
            assert "registry" in rec
            assert rec["registry"] in {"pypi", "npm"}
            assert rec["label"] == "malicious"
            assert "collected_at" in rec
            assert "attack_type" in rec

    def test_idempotent_skip(self, tmp_path: Path) -> None:
        from data.datasets.download_backstabbers import download_backstabbers_dataset

        records1 = download_backstabbers_dataset(output_dir=str(tmp_path), force=True)
        records2 = download_backstabbers_dataset(output_dir=str(tmp_path), force=False)
        assert len(records1) == len(records2)

    def test_no_duplicates(self, tmp_path: Path) -> None:
        from data.datasets.download_backstabbers import download_backstabbers_dataset

        records = download_backstabbers_dataset(output_dir=str(tmp_path), force=True)
        keys = [(r["package_name"], r["registry"]) for r in records]
        assert len(keys) == len(set(keys)), "Duplicate records detected"


class TestLabelAndSplit:
    @pytest.fixture()
    def _seed_files(self, tmp_path: Path) -> tuple[str, str, str]:
        """Create minimal malicious + benign JSON files for testing."""
        malicious = [
            {"package_name": f"mal-{i}", "registry": "pypi", "label": "malicious"}
            for i in range(10)
        ]
        benign = [
            {"package_name": f"good-{i}", "registry": "pypi", "label": "benign"}
            for i in range(40)
        ]
        mal_path = str(tmp_path / "malicious.json")
        ben_path = str(tmp_path / "benign.json")
        out_dir = str(tmp_path / "splits")

        with open(mal_path, "w") as f:
            json.dump(malicious, f)
        with open(ben_path, "w") as f:
            json.dump(benign, f)

        return mal_path, ben_path, out_dir

    def test_creates_three_split_files(self, _seed_files: tuple[str, str, str]) -> None:
        from data.datasets.label_and_split import label_and_split

        mal_path, ben_path, out_dir = _seed_files
        stats = label_and_split(
            malicious_path=mal_path, benign_path=ben_path,
            output_dir=out_dir, seed=42, force=True,
        )
        assert stats["total"] == 50
        assert stats["train"] + stats["val"] + stats["test"] == 50
        for name in ("train.json", "val.json", "test.json"):
            assert Path(out_dir, name).exists()

    def test_deterministic_with_seed(self, _seed_files: tuple[str, str, str]) -> None:
        from data.datasets.label_and_split import label_and_split

        mal_path, ben_path, out_dir = _seed_files
        label_and_split(malicious_path=mal_path, benign_path=ben_path,
                        output_dir=out_dir, seed=42, force=True)
        with open(Path(out_dir) / "train.json") as f:
            run1 = json.load(f)

        label_and_split(malicious_path=mal_path, benign_path=ben_path,
                        output_dir=out_dir, seed=42, force=True)
        with open(Path(out_dir) / "train.json") as f:
            run2 = json.load(f)

        assert run1 == run2, "Splits should be deterministic with same seed"

    def test_both_classes_in_each_split(self, _seed_files: tuple[str, str, str]) -> None:
        from data.datasets.label_and_split import label_and_split

        mal_path, ben_path, out_dir = _seed_files
        label_and_split(malicious_path=mal_path, benign_path=ben_path,
                        output_dir=out_dir, seed=42, force=True)

        with open(Path(out_dir) / "train.json") as f:
            train = json.load(f)

        labels = {r["label"] for r in train}
        assert "malicious" in labels
        assert "benign" in labels


class TestTopPackages:
    def test_pypi_top_1000_has_entries(self) -> None:
        path = _TOP_PACKAGES_DIR / "pypi_top_1000.json"
        assert path.exists(), "pypi_top_1000.json missing"
        with open(path) as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) >= 100, f"Expected >=100, got {len(data)}"

    def test_npm_top_1000_has_entries(self) -> None:
        path = _TOP_PACKAGES_DIR / "npm_top_1000.json"
        assert path.exists(), "npm_top_1000.json missing"
        with open(path) as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) >= 100, f"Expected >=100, got {len(data)}"

    def test_pypi_entries_have_name_field(self) -> None:
        path = _TOP_PACKAGES_DIR / "pypi_top_1000.json"
        with open(path) as f:
            data = json.load(f)
        for entry in data[:10]:
            if isinstance(entry, dict):
                assert "name" in entry

    def test_npm_entries_have_name_field(self) -> None:
        path = _TOP_PACKAGES_DIR / "npm_top_1000.json"
        with open(path) as f:
            data = json.load(f)
        for entry in data[:10]:
            if isinstance(entry, dict):
                assert "name" in entry
