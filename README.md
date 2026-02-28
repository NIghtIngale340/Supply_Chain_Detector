# Supply Chain Detector

AI-powered software supply chain attack detector focused on PyPI and npm package pre-installation risk analysis.

## Overview

This project builds a local-first analysis pipeline to identify potential supply chain risk signals in third-party packages before installation.

Initial focus:

1. Collect package metadata from PyPI and npm
2. Download and safely extract package source archives
3. Normalize records into a consistent dataset format
4. Feed features into layered detectors for risk scoring

## Detection Scope

- Metadata-based indicators (author, version, typosquat patterns)
- Dataset preparation for benign and malicious package comparison
- Extensible architecture for static analysis and model-assisted review in later phases

## Quick Start

1. Install Python 3.11+
2. Install Poetry
3. Install Docker Desktop (for later phases, optional in Phase 1)
4. Run:

```powershell
poetry install
copy .env.example .env
poetry run ruff check .
poetry run pytest -q
```

## Phase 6 + 7 Runtime (API, Worker, UI, CI)

Bring up the local stack:

```powershell
copy .env.example .env
docker compose up --build
```

Run API and worker without Docker:

```powershell
poetry run uvicorn api.main:app --reload --port 8000
poetry run celery -A api.celery_app.celery_app worker --loglevel=info
```

Run Streamlit dashboard:

```powershell
poetry run streamlit run ui/streamlit_app.py
```

## API Endpoints

- `GET /health` returns service status
- `POST /analyze` accepts `{name, registry}` and returns a queued `job_id`
- `GET /results/{job_id}` returns pending/completed analysis status

## Layer 5 Graph Features

- Dependency graph builder with bounded recursion and cycle protection
- Distance-decayed transitive risk propagation
- Blast radius calculation over reverse dependencies
- Notebook visualization checkpoint in `notebooks/06_layer5_graph_visualization.ipynb`

## GitHub Action Scanner

Custom action assets are in `github_action/`:

- `action.yml`
- `entrypoint.sh`
- `scan_requirements.py`

The action parses `requirements.txt` and `package.json`, calls the API for each dependency, and fails the workflow when scores cross a configurable threshold.

## Project Layout

```text
supply-chain-detector/
├── fetcher/
├── detector/
│   └── layer5_graph/
├── api/
├── workers/
├── ui/
├── github_action/
├── docker-compose.yml
├── data/
│   ├── datasets/
│   ├── raw/
│   └── processed/
├── tests/
├── notebooks/
├── docs/
│   └── phases/
├── pyproject.toml
└── README.md
```
