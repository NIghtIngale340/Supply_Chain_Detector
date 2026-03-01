from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import requests

from api.cache import get_json, set_json
from api.config import get_settings
from detector.orchestrator import orchestrate_analysis
from fetcher.source_extractor import extract_archive
from fetcher.npm_fetcher import fetch_npm_metadata
from fetcher.pypi_fetcher import fetch_pypi_metadata
from storage.repository import upsert_scan_job


_MAX_SOURCE_CHARS = 120_000
_MAX_SOURCE_FILES = 30
_TEXT_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".ts",
    ".tsx",
}


def _fetch_metadata(name: str, registry: str) -> dict:
    cache_key = f"scd:metadata:{registry}:{name}"
    settings = get_settings()
    cached = get_json(cache_key)
    if cached is not None:
        if registry == "pypi" and not str(cached.get("dist_tarball", "")).strip():
            cached = None
        else:
            return cached

    if registry == "pypi":
        result = fetch_pypi_metadata(name)
    else:
        result = fetch_npm_metadata(name)
    if result.status_code != 200:
        raise ValueError(f"Failed to fetch metadata for {name} from {registry}")
    set_json(cache_key, result.metadata, settings.cache_ttl_seconds)
    return result.metadata


def _build_metadata_context(name: str, registry: str, metadata: dict[str, Any]) -> str:
    dependencies = metadata.get("dependencies") or metadata.get("requires_dist") or []
    return "\n".join(
        [
            f"package={name}",
            f"registry={registry}",
            f"version={metadata.get('version', '')}",
            f"author={metadata.get('author', '')}",
            f"summary={metadata.get('summary', metadata.get('description', ''))}",
            f"dependencies={dependencies}",
            f"source_url={metadata.get('dist_tarball', metadata.get('source_url', ''))}",
        ]
    )


def _extract_archive_url(metadata: dict[str, Any]) -> str:
    tarball = str(metadata.get("dist_tarball", "")).strip()
    if tarball:
        return tarball
    return str(metadata.get("source_url", "")).strip()


def _download_archive(url: str, destination: Path) -> Path:
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    file_name = url.split("?")[0].rstrip("/").split("/")[-1] or "package.tgz"
    archive_path = destination / file_name
    with open(archive_path, "wb") as file:
        file.write(response.content)
    return archive_path


def _collect_source_context(source_root: Path) -> str:
    snippets: list[str] = []
    chars_collected = 0
    files_collected = 0

    for file_path in sorted(source_root.rglob("*")):
        if not file_path.is_file() or file_path.suffix.lower() not in _TEXT_EXTENSIONS:
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        if not content.strip():
            continue

        header = f"\n# file: {file_path.relative_to(source_root).as_posix()}\n"
        remaining = _MAX_SOURCE_CHARS - chars_collected
        if remaining <= 0:
            break

        bounded_content = content[: max(0, remaining - len(header))]
        chunk = header + bounded_content
        snippets.append(chunk)
        chars_collected += len(chunk)
        files_collected += 1

        if files_collected >= _MAX_SOURCE_FILES or chars_collected >= _MAX_SOURCE_CHARS:
            break

    return "\n".join(snippets).strip()


def _build_source_inputs(
    name: str,
    registry: str,
    metadata: dict[str, Any],
    temp_dir: Path,
) -> tuple[str, str | None, list[str]]:
    warnings: list[str] = []
    archive_url = _extract_archive_url(metadata)
    if not archive_url:
        warnings.append("Archive URL unavailable; using metadata-only context")
        return _build_metadata_context(name, registry, metadata), None, warnings

    try:
        archive_path = _download_archive(archive_url, temp_dir)
        extracted_path = extract_archive(archive_path, temp_dir)
        source_context = _collect_source_context(extracted_path)
        if source_context:
            return source_context, str(extracted_path), warnings
        warnings.append("Source archive extracted but no supported source files were collected")
    except Exception as exc:
        warnings.append(f"Failed to download/extract source archive: {exc}")

    return _build_metadata_context(name, registry, metadata), None, warnings


def run_analysis_for_package(name: str, registry: str, job_id: str | None = None) -> dict[str, Any]:
    normalized_name = name.strip().lower()
    metadata = _fetch_metadata(normalized_name, registry)
    with tempfile.TemporaryDirectory(prefix="scd_source_") as temp_dir:
        source_context, source_path, source_warnings = _build_source_inputs(
            normalized_name,
            registry,
            metadata,
            Path(temp_dir),
        )

        result = orchestrate_analysis(
            package_name=normalized_name,
            registry=registry,
            metadata=metadata,
            source_context=source_context,
            source_path=source_path,
        )

    if source_warnings:
        result["runtime_warnings"] = source_warnings

    if job_id:
        upsert_scan_job(
            job_id=job_id,
            package_name=normalized_name,
            registry=registry,
            status="completed",
            payload=result,
        )

    return result
