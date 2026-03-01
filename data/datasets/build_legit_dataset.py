

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Add project root for imports when run as a script
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


PYPI_TOP_PACKAGES_URL = "https://hugovk.github.io/top-pypi-packages/top-pypi-packages-30-days.min.json"


NPM_SEARCH_URL = "https://registry.npmjs.org/-/v1/search"


def _fetch_with_retry(url: str, params: dict | None = None, max_retries: int = 3) -> dict | None:
    """GET JSON with exponential back-off."""
    import requests

    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            wait = 2 ** attempt
            logger.warning("Attempt %d/%d failed for %s: %s — retrying in %ds",
                           attempt + 1, max_retries, url, exc, wait)
            time.sleep(wait)
    logger.error("All %d attempts failed for %s", max_retries, url)
    return None


def fetch_top_pypi(count: int = 200) -> list[dict]:
    logger.info("Fetching top %d PyPI packages …", count)
    data = _fetch_with_retry(PYPI_TOP_PACKAGES_URL)
    if data is None:
        logger.error("Could not reach PyPI top-packages endpoint")
        return []

    rows = data.get("rows", [])[:count]
    results = []
    for row in rows:
        project = row.get("project", "")
        downloads = row.get("download_count", 0)
        if project:
            results.append({"name": project, "downloads": downloads})
    logger.info("Collected %d PyPI packages", len(results))
    return results


def fetch_top_npm(count: int = 200) -> list[dict]:
    logger.info("Fetching top %d npm packages …", count)
    results: list[dict] = []
    seen: set[str] = set()
    page_size = min(count, 250)
    offset = 0

    while len(results) < count:
        params = {"text": "keywords:javascript", "size": page_size, "from": offset,
                  "quality": "0.0", "popularity": "1.0", "maintenance": "0.0"}
        data = _fetch_with_retry(NPM_SEARCH_URL, params=params)
        if data is None:
            break
        objects = data.get("objects", [])
        if not objects:
            break

        for obj in objects:
            pkg = obj.get("package", {})
            name = pkg.get("name", "")
            if name and name not in seen:
                seen.add(name)
                results.append({"name": name, "downloads": 0})
            if len(results) >= count:
                break

        offset += page_size
        time.sleep(1.0)  # rate-limit

    logger.info("Collected %d npm packages", len(results))
    return results


def build_legit_dataset(
    output_dir: str = "data/processed",
    count: int = 200,
    registry: str = "both",
    force: bool = False,
) -> list[dict]:
   
    output_file = os.path.join(output_dir, "benign_dataset.json")

    if os.path.exists(output_file) and not force:
        logger.info("Output exists at %s — skipping (use --force to overwrite)", output_file)
        with open(output_file, "r", encoding="utf-8") as f:
            return json.load(f)

    os.makedirs(output_dir, exist_ok=True)
    collected_at = datetime.now(timezone.utc).isoformat()
    records: list[dict] = []

    if registry in ("pypi", "both"):
        for pkg in fetch_top_pypi(count):
            records.append({
                "package_name": pkg["name"],
                "registry": "pypi",
                "label": "benign",
                "source": "top_pypi_packages",
                "downloads": pkg.get("downloads", 0),
                "collected_at": collected_at,
            })

    if registry in ("npm", "both"):
        for pkg in fetch_top_npm(count):
            records.append({
                "package_name": pkg["name"],
                "registry": "npm",
                "label": "benign",
                "source": "top_npm_packages",
                "downloads": pkg.get("downloads", 0),
                "collected_at": collected_at,
            })

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    logger.info("Wrote %d benign records to %s", len(records), output_file)
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Build legitimate (benign) package dataset")
    parser.add_argument("--output-dir", default="data/processed", help="Output directory")
    parser.add_argument("--count", type=int, default=200, help="Packages per registry to fetch")
    parser.add_argument("--registry", choices=["pypi", "npm", "both"], default="both")
    parser.add_argument("--force", action="store_true", help="Overwrite existing output")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    records = build_legit_dataset(
        output_dir=args.output_dir,
        count=args.count,
        registry=args.registry,
        force=args.force,
    )
    print(f"{len(records)} benign records ready in {args.output_dir}")


if __name__ == "__main__":
    main()
