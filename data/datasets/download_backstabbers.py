"""Download and normalize the backstabbers-knife-collection malicious-package dataset.

This script builds a local seed of documented malicious packages sourced from
the IQTLabs Backstabbers-Knife-Collection research repository and other public
supply-chain incident reports.

Usage:
    python -m data.datasets.download_backstabbers          # default output
    python data/datasets/download_backstabbers.py --force   # overwrite existing
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Curated seed — 30 documented malicious packages across PyPI and npm
# ---------------------------------------------------------------------------
MALICIOUS_SEED: list[dict] = [
    # --- PyPI typosquats ---
    {"package_name": "colourama",          "registry": "pypi", "attack_type": "typosquat",            "notes": "Typosquat of colorama — credential stealer"},
    {"package_name": "python-dateutils",   "registry": "pypi", "attack_type": "typosquat",            "notes": "Typosquat of python-dateutil"},
    {"package_name": "jeIlyfish",          "registry": "pypi", "attack_type": "typosquat",            "notes": "Typosquat of jellyfish (capital I instead of l)"},
    {"package_name": "python3-dateutil",   "registry": "pypi", "attack_type": "typosquat",            "notes": "Typosquat of python-dateutil — data exfiltration"},
    {"package_name": "numpyy",             "registry": "pypi", "attack_type": "typosquat",            "notes": "Typosquat of numpy"},
    {"package_name": "requesocks",         "registry": "pypi", "attack_type": "typosquat",            "notes": "Typosquat of requests"},
    {"package_name": "openvc",             "registry": "pypi", "attack_type": "typosquat",            "notes": "Typosquat of opencv-python"},
    {"package_name": "colourama",          "registry": "pypi", "attack_type": "typosquat",            "notes": "Typosquat/credential stealer"},
    {"package_name": "dlogging",           "registry": "pypi", "attack_type": "typosquat",            "notes": "Typosquat of logging — reverse shell"},
    {"package_name": "crypt",              "registry": "pypi", "attack_type": "typosquat",            "notes": "Typosquat of cryptography"},
    # --- PyPI setup.py exec ---
    {"package_name": "libpeshka",          "registry": "pypi", "attack_type": "setup_exec",           "notes": "Malicious setup.py exec during pip install"},
    {"package_name": "mongoxclient",       "registry": "pypi", "attack_type": "setup_exec",           "notes": "Fake MongoDB client — exec in setup.py"},
    {"package_name": "discordspy",         "registry": "pypi", "attack_type": "credential_harvester",  "notes": "Fake Discord library — steals Discord tokens"},
    {"package_name": "colorwin",           "registry": "pypi", "attack_type": "credential_harvester",  "notes": "Credential harvesting via os.environ"},
    {"package_name": "pydefender",         "registry": "pypi", "attack_type": "reverse_shell",         "notes": "Reverse shell on import"},
    # --- npm incidents ---
    {"package_name": "event-stream",       "registry": "npm",  "attack_type": "dependency_hijack",     "notes": "flatmap-stream injected a Bitcoin wallet stealer"},
    {"package_name": "ua-parser-js",       "registry": "npm",  "attack_type": "account_hijack",        "notes": "Maintainer account compromised — crypto-miner + credential stealer"},
    {"package_name": "coa",                "registry": "npm",  "attack_type": "account_hijack",        "notes": "Compromised maintainer pushed malicious version"},
    {"package_name": "rc",                 "registry": "npm",  "attack_type": "account_hijack",        "notes": "Compromised maintainer — credential theft"},
    {"package_name": "colors",             "registry": "npm",  "attack_type": "maintainer_sabotage",   "notes": "Author intentionally corrupted output (protest-ware)"},
    {"package_name": "faker",              "registry": "npm",  "attack_type": "maintainer_sabotage",   "notes": "Same maintainer sabotage as colors"},
    {"package_name": "crossenv",           "registry": "npm",  "attack_type": "typosquat",             "notes": "Typosquat of cross-env — credential stealer"},
    {"package_name": "getcookies",         "registry": "npm",  "attack_type": "hidden_backdoor",       "notes": "Hidden backdoor activated via HTTP headers"},
    {"package_name": "flatmap-stream",     "registry": "npm",  "attack_type": "dependency_hijack",     "notes": "Injected into event-stream — targeted Copay wallet"},
    {"package_name": "eslint-scope",       "registry": "npm",  "attack_type": "account_hijack",        "notes": "npm token stolen — credential harvester injected"},
    {"package_name": "mailparser",         "registry": "npm",  "attack_type": "account_hijack",        "notes": "Compromised — credential exfiltration"},
    {"package_name": "twilio-npm",         "registry": "npm",  "attack_type": "typosquat",             "notes": "Typosquat of twilio — reverse shell on install"},
    {"package_name": "discord.js-user",    "registry": "npm",  "attack_type": "typosquat",             "notes": "Typosquat of discord.js — token stealer"},
    {"package_name": "electorn",           "registry": "npm",  "attack_type": "typosquat",             "notes": "Typosquat of electron"},
    {"package_name": "loadyaml",           "registry": "npm",  "attack_type": "typosquat",             "notes": "Typosquat of js-yaml"},
]

SOURCE_REFERENCE = "https://github.com/IQTLabs/Backstabbers-Knife-Collection"


def download_backstabbers_dataset(
    output_dir: str = "data/processed",
    force: bool = False,
) -> list[dict]:
    """Build the malicious-package seed file.

    Returns the list of records written.
    """
    output_file = os.path.join(output_dir, "backstabbers_seed.json")

    if os.path.exists(output_file) and not force:
        logger.info("Output already exists at %s — skipping (use --force to overwrite)", output_file)
        with open(output_file, "r", encoding="utf-8") as f:
            return json.load(f)

    os.makedirs(output_dir, exist_ok=True)

    collected_at = datetime.now(timezone.utc).isoformat()

    records: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for entry in MALICIOUS_SEED:
        key = (entry["package_name"], entry["registry"])
        if key in seen:
            logger.debug("Duplicate skipped: %s/%s", entry["registry"], entry["package_name"])
            continue
        seen.add(key)
        records.append(
            {
                "package_name": entry["package_name"],
                "registry": entry["registry"],
                "label": "malicious",
                "attack_type": entry.get("attack_type", "unknown"),
                "source_reference": SOURCE_REFERENCE,
                "notes": entry.get("notes", ""),
                "collected_at": collected_at,
            }
        )

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    logger.info("Wrote %d malicious-package records to %s", len(records), output_file)
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Download backstabbers malicious package dataset")
    parser.add_argument("--output-dir", default="data/processed", help="Directory for output JSON")
    parser.add_argument("--force", action="store_true", help="Overwrite existing output file")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    records = download_backstabbers_dataset(output_dir=args.output_dir, force=args.force)
    print(f"{len(records)} malicious-package records ready in {args.output_dir}")


if __name__ == "__main__":
    main()