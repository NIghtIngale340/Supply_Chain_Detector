# Development Setup (Windows + Poetry)

## Why this setup

- Python 3.11 gives broad package compatibility.
- Poetry gives deterministic dependency and virtual environment management.
- Docker is installed early for later multi-service phases, but Phase 1 remains Python-only.

## Prerequisites

1. Python 3.11+
2. Git
3. Poetry
4. Docker Desktop (running)

## Verify tools

```powershell
python --version
git --version
poetry --version
docker --version
```

## Python version policy

- Target baseline: Python 3.11+
- Temporary fallback: Python 3.10 can be used only for Phase 1 scaffolding if needed.
- Upgrade checkpoint: before Phase 2 starts, install Python 3.11 and recreate the environment.

## Install dependencies

```powershell
poetry install
copy .env.example .env
```

## Validate baseline

```powershell
poetry run ruff check .
poetry run pytest -q
```

If Poetry is unavailable in your shell path, run commands through Python directly:

```powershell
python -m ruff check .
python -m pytest -q
```

## Best practices

- Keep `data/raw` and `data/processed` out of git except placeholders.
- Treat API keys as secrets: use `.env`, never commit real values.
- Add one small test for each new script before scaling data volume.
- Prefer deterministic scripts (same input -> same output) for reproducibility.
