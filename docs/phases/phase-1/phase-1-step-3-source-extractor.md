# Phase 1 — Step 3: Implement Source Extractor

## Why this step now

Fetching metadata is only half the pipeline. You need source files extracted locally for later static and embedding analysis layers.

## Your coding target

Implement `extract_archive(archive_path: Path, output_dir: Path) -> Path` in `fetcher/source_extractor.py`.

## Contract (must satisfy)

Input:

- `archive_path: Path` to existing archive
- `output_dir: Path` destination directory

Output:

- Returns `Path` to extraction root directory

Behavior:

- Supports `.tar.gz`, `.tgz`, `.zip`, `.whl`
- Creates destination directory if missing
- Prevents path traversal attacks during extraction
- Raises clear exception for unsupported or invalid archives

## Implementation notes (best practices)

1. Validate inputs
   - archive exists and is a file
2. Infer archive type by suffix
3. Create deterministic extraction folder
   - e.g., `{output_dir}/{archive_stem}`
4. Add safe extraction checks
   - ensure members cannot escape target dir
5. Keep function side effects minimal

## Suggested mini-checklist while coding

- [ ] Validate file existence/type
- [ ] Create output directory
- [ ] Implement tar extraction path safety
- [ ] Implement zip/whl extraction path safety
- [ ] Return extraction root path

## Manual validation commands

```powershell
python -c "from pathlib import Path; from fetcher.source_extractor import extract_archive; p=extract_archive(Path('data/raw/sample.tgz'), Path('data/raw/extracted')); print(p)"
```

Expected:

- extraction folder path is printed
- extracted files exist under that folder

## Edge cases to handle now

- corrupted archive
- archive has nested top-level folder or no top-level folder
- duplicate extraction target already exists

## Done criteria for Step 3

- Successfully extracts at least one `.tgz` and one `.whl/.zip`
- Blocks unsafe archive member paths
- Lint/tests pass

```powershell
python -m ruff check .
python -m pytest -q
```

## Mentor tip

Security starts here. Safe extraction is not optional in a supply-chain project.
