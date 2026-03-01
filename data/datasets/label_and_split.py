

from __future__ import annotations

import argparse
import json
import logging
import os
import random
from collections import Counter

logger = logging.getLogger(__name__)


def _load_json(path: str) -> list[dict]:
    if not os.path.exists(path):
        logger.warning("File not found: %s", path)
        return []
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        logger.warning("Expected list in %s, got %s", path, type(data).__name__)
        return []
    return data


def _stratified_split(
    records: list[dict],
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    seed: int = 42,
) -> tuple[list[dict], list[dict], list[dict]]:
    rng = random.Random(seed)

    by_label: dict[str, list[dict]] = {}
    for rec in records:
        label = rec.get("label", "unknown")
        by_label.setdefault(label, []).append(rec)

    train: list[dict] = []
    val: list[dict] = []
    test: list[dict] = []

    for label, group in by_label.items():
        rng.shuffle(group)
        n = len(group)
        n_train = max(1, int(n * train_ratio))
        n_val = max(1, int(n * val_ratio))
        # rest goes to test
        train.extend(group[:n_train])
        val.extend(group[n_train : n_train + n_val])
        test.extend(group[n_train + n_val :])

    # shuffle each split (deterministic)
    rng.shuffle(train)
    rng.shuffle(val)
    rng.shuffle(test)

    return train, val, test


def label_and_split(
    malicious_path: str = "data/processed/backstabbers_seed.json",
    benign_path: str = "data/processed/benign_dataset.json",
    output_dir: str = "data/processed/splits",
    seed: int = 42,
    force: bool = False,
) -> dict:
    train_file = os.path.join(output_dir, "train.json")
    if os.path.exists(train_file) and not force:
        logger.info("Splits already exist in %s — skipping (use --force)", output_dir)
        return {"skipped": True}

    malicious = _load_json(malicious_path)
    benign = _load_json(benign_path)

    if not malicious:
        alt = malicious_path.replace("backstabbers_seed", "malicious_normalized")
        malicious = _load_json(alt)

    if not benign:
        alt = benign_path.replace("benign_dataset", "benign_sample")
        benign = _load_json(alt)

    for rec in malicious:
        rec.setdefault("label", "malicious")
    for rec in benign:
        rec.setdefault("label", "benign")

    combined = malicious + benign
    if not combined:
        logger.error("No records found — nothing to split")
        return {"error": "empty_dataset"}

    label_counts = Counter(r["label"] for r in combined)
    logger.info("Combined dataset: %d records — %s", len(combined), dict(label_counts))

    train, val, test = _stratified_split(combined, seed=seed)

    os.makedirs(output_dir, exist_ok=True)
    for name, data in [("train.json", train), ("val.json", val), ("test.json", test)]:
        path = os.path.join(output_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    stats = {
        "total": len(combined),
        "label_distribution": dict(label_counts),
        "train": len(train),
        "val": len(val),
        "test": len(test),
        "seed": seed,
    }
    logger.info("Splits: train=%d val=%d test=%d (seed=%d)", len(train), len(val), len(test), seed)
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Combine and split malicious/benign datasets")
    parser.add_argument(
        "--malicious", default="data/processed/backstabbers_seed.json",
        help="Path to malicious records JSON",
    )
    parser.add_argument(
        "--benign", default="data/processed/benign_dataset.json",
        help="Path to benign records JSON",
    )
    parser.add_argument("--output-dir", default="data/processed/splits", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic splits")
    parser.add_argument("--force", action="store_true", help="Overwrite existing split files")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    stats = label_and_split(
        malicious_path=args.malicious,
        benign_path=args.benign,
        output_dir=args.output_dir,
        seed=args.seed,
        force=args.force,
    )
    print(f"Split stats: {json.dumps(stats, indent=2)}")


if __name__ == "__main__":
    main()
