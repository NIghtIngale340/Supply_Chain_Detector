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

    urls = info.get("project_urls") or {}

    metadata = {
        "name":          info.get("name", ""),
        "version":       info.get("version", ""),
        "summary":       info.get("summary", ""),
        "author":        info.get("author", ""),
        "license":       info.get("license", ""),
        "project_urls":  urls,  
        "requires_dist": info.get("requires_dist", []),
        "source_url":    urls.get("Source") or urls.get("Homepage", ""),
    }

    
    return FetchResult(
        package_name=package_name,
        registry="pypi",    
        status_code=response.status_code,
        metadata=metadata, 
    )
