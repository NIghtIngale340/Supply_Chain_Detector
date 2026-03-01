import sys
import tarfile
import zipfile
from pathlib import Path


def _is_safe_path(member_path: str, target_dir: Path) -> bool:
    resolved = (target_dir / member_path).resolve()
    try:
        resolved.relative_to(target_dir.resolve())
        return True
    except ValueError:
        return False


def _safe_tar_extractall(tar: tarfile.TarFile, path: Path) -> None:
    """Extract tar with filter='data' on Python >= 3.12, manual check otherwise."""
    for member in tar.getmembers():
        if not _is_safe_path(member.name, path):
            raise ValueError(f"Unsafe path in archive: {member.name}")
    if sys.version_info >= (3, 12):
        tar.extractall(path=path, filter="data")
    else:
        tar.extractall(path=path)


def extract_archive(archive_path: Path, output_dir: Path) -> Path:
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")
    if not archive_path.is_file():
        raise ValueError(f"Not a file: {archive_path}")
    stem = archive_path.stem
    if stem.endswith(".tar"):
        stem = stem[:-4]
    extract_dir = output_dir / stem
    extract_dir.mkdir(parents=True, exist_ok=True)

    suffix = archive_path.suffix.lower()
    suffixes = [s.lower() for s in archive_path.suffixes]

    is_tar_gz = suffixes[-2:] == [".tar", ".gz"]
    if suffix in (".tgz",) or is_tar_gz:
        with tarfile.open(archive_path, "r:gz") as tar:
            _safe_tar_extractall(tar, extract_dir)

    elif suffix in (".zip", ".whl"):
        with zipfile.ZipFile(archive_path, "r") as zf:
            for name in zf.namelist():
                if not _is_safe_path(name, extract_dir):
                    raise ValueError(f"Unsafe path in archive: {name}")
            zf.extractall(path=extract_dir)

    else:
        raise ValueError(f"Unsupported archive format: {archive_path.name}")

    return extract_dir
