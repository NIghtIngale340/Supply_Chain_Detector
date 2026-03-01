import os
from dataclasses import dataclass
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()


@dataclass
class FetchResult:
    package_name: str
    registry: str
    status_code: int
    metadata: dict


def fetch_pypi_metadata(package_name: str) -> FetchResult:
    if not package_name.strip():
        raise ValueError("Package name cannot be empty")

   
    base_url = os.getenv("PYPI_BASE_URL", "https://pypi.org/pypi")
    url = f"{base_url}/{package_name}/json"

    
    try:
        response = requests.get(url, timeout=10)
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Network error fetching {package_name}: {e}")

    
    if response.status_code != 200:
        return FetchResult(
            package_name=package_name,
            registry=   "pypi",
            status_code=response.status_code,
            metadata={},
        )

    
    data = response.json()
    info = data.get("info", {})
    releases = data.get("releases", {})
    latest_files = data.get("urls", []) if isinstance(data.get("urls"), list) else []

    dist_tarball = ""
    for file_info in latest_files:
        if not isinstance(file_info, dict):
            continue
        packagetype = str(file_info.get("packagetype", "")).lower()
        if packagetype == "sdist" and file_info.get("url"):
            dist_tarball = str(file_info["url"])
            break
    if not dist_tarball:
        for file_info in latest_files:
            if isinstance(file_info, dict) and file_info.get("url"):
                dist_tarball = str(file_info["url"])
                break

    urls = info.get("project_urls") or {}

    release_history = []
    for version, files in releases.items():
        if not files:
            continue
        first = files[0]
        release_history.append({"version": version, "date": first.get("upload_time_iso_8601") or first.get("upload_time")})

    created_at = None
    if release_history:
        parsed = [entry.get("date") for entry in release_history if entry.get("date")]
        created_at = min(parsed) if parsed else None

    metadata = {
        "name":          info.get("name", ""),
        "version":       info.get("version", ""),
        "summary":       info.get("summary", ""),
        "author":        info.get("author", ""),
        "license":       info.get("license", ""),
        "project_urls":  urls,  
        "requires_dist": info.get("requires_dist", []),
        "created_at": created_at,
        "release_history": release_history,
        "published_count": len(releases),
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "source_url":    urls.get("Source") or urls.get("Homepage", ""),
        "dist_tarball":  dist_tarball,
    }

    
    return FetchResult(
        package_name=package_name,
        registry="pypi",    
        status_code=response.status_code,
        metadata=metadata, 
    )
