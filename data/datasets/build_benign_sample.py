import json
import os
from datetime import datetime, timezone

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from fetcher.pypi_fetcher import fetch_pypi_metadata
from fetcher.npm_fetcher import fetch_npm_metadata


PYPI_BENIGN = [
    "requests", "flask", "django", "numpy", "pandas",
    "scipy", "matplotlib", "pillow", "sqlalchemy", "celery",
    "pytest", "black", "mypy", "pydantic", "fastapi",
    "httpx", "uvicorn", "gunicorn", "boto3", "click",
]
NPM_BENIGN = [
    "lodash", "express", "react", "axios", "moment",
    "chalk", "commander", "debug", "uuid", "dotenv",
    "webpack", "typescript", "eslint", "prettier", "jest",
    "next", "vue", "cors", "mongoose", "jsonwebtoken",
]


def build_benign_sample() -> None:
    output_dir = "data/processed"
    output_file = os.path.join(output_dir, "benign_sample.json")

    os.makedirs(output_dir, exist_ok=True)

    collected_at = datetime.now(timezone.utc).isoformat()

    records = []
    seen = set()

    
    for pkg_name in PYPI_BENIGN:
        key = ("pypi", pkg_name)
        if key in seen:
            continue

        try:
            result = fetch_pypi_metadata(pkg_name)
            if result.status_code != 200:
                print(f"  Skipping {pkg_name}: HTTP {result.status_code}")
                continue
        except Exception as e:
            print(f"  Error fetching {pkg_name}: {e}")
            continue

        seen.add(key)
        records.append({
            "package_name": pkg_name,
            "registry": "pypi",
            "source": "top_pypi_packages",
            "label": "benign",
            "collected_at": collected_at,
        })
        print(f" {pkg_name}")

 
    for pkg_name in NPM_BENIGN:
        key = ("npm", pkg_name)
        if key in seen:
            continue

        try:
            result = fetch_npm_metadata(pkg_name)
            if result.status_code != 200:
                print(f"  Skipping {pkg_name}: HTTP {result.status_code}")
                continue
        except Exception as e:
            print(f"  Error fetching {pkg_name}: {e}")
            continue

        seen.add(key)
        records.append({
            "package_name": pkg_name,
            "registry": "npm",
            "source": "top_npm_packages",
            "label": "benign",
            "collected_at": collected_at,
        })
        print(f" {pkg_name}")

    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(records)} benign records to {output_file}")\


if __name__ == "__main__":
    print("Building benign sample dataset...")
    build_benign_sample()








   

    
