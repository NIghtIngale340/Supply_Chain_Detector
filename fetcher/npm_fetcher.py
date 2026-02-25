import os
from dataclasses import dataclass

import requests
from dotenv import load_dotenv

load_dotenv()


@dataclass
class FetchResult:
    package_name: str
    registry: str
    status_code: int
    metadata: dict


def fetch_npm_metadata(package_name: str) -> FetchResult:
    
    if not package_name.strip():
        raise ValueError("Package name cannot be empty")

   
    base_url = os.getenv("NPM_BASE_URL", "https://registry.npmjs.org")
    url = f"{base_url}/{package_name.strip()}"

    try:
        response = requests.get(url, timeout=10)
    except requests.RequestException as e:
        raise ConnectionError(f"Network error fetching {package_name}: {e}")

   
    if response.status_code != 200:
        return FetchResult(
            package_name=package_name,
            registry=base_url,
            status_code=response.status_code,
            metadata={},
        )

   
    data = response.json()

    latest_version = data.get("dist-tags", {}).get("latest", "")
    version_info = data.get("versions", {}).get(latest_version, {})

    repo_raw = data.get("repository", {})
    if isinstance(repo_raw, dict):
        repository = repo_raw.get("url", "")
    else:
        repository = str(repo_raw) if repo_raw else ""

    author_raw = data.get("author", {})
    if isinstance(author_raw, dict):
        author = author_raw.get("name", "")
    else:
        author = str(author_raw) if author_raw else ""

    metadata = {
        "name":          data.get("name", ""),
        "version":       latest_version,
        "description":   data.get("description", ""),
        "author":        author,
        "license":       data.get("license", ""),
        "repository":    repository,
        "homepage":      data.get("homepage", ""),
        "dependencies":  version_info.get("dependencies", {}),
        "dist_tarball":  version_info.get("dist", {}).get("tarball", ""),
    }

    
    return FetchResult(
        package_name=package_name,
        registry=base_url,
        status_code=response.status_code,
        metadata=metadata,
    )
