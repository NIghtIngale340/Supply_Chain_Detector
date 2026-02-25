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

## Project Layout

```text
supply-chain-detector/
├── fetcher/
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
