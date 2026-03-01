"""Generate all datasets, train XGBoost, and build FAISS index.

Runs the full data pipeline end-to-end without network access by using
the curated malicious seed and synthesising realistic benign records.

Usage:
    python -m data.datasets.generate_all_data          # default
    python data/datasets/generate_all_data.py --force   # overwrite existing
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# ---------------------------------------------------------------------------
# Synthetic benign records — realistic metadata for well-known safe packages
# ---------------------------------------------------------------------------
SYNTHETIC_BENIGN: list[dict] = [
    # --- PyPI packages ---
    {"package_name": "requests", "registry": "pypi", "version": "2.31.0",
     "author": "Kenneth Reitz", "summary": "HTTP library for Python",
     "requires_dist": ["charset-normalizer", "idna", "urllib3", "certifi"],
     "source_code": "import urllib3\ndef get(url, **kwargs):\n    return session.request('GET', url, **kwargs)\n"},
    {"package_name": "flask", "registry": "pypi", "version": "3.0.0",
     "author": "Pallets", "summary": "Lightweight WSGI web framework",
     "requires_dist": ["werkzeug", "jinja2", "itsdangerous", "click", "blinker"],
     "source_code": "from werkzeug.serving import run_simple\nclass Flask:\n    def run(self, host='127.0.0.1', port=5000):\n        run_simple(host, port, self)\n"},
    {"package_name": "django", "registry": "pypi", "version": "5.0",
     "author": "Django Software Foundation", "summary": "High-level Python web framework",
     "requires_dist": ["asgiref", "sqlparse"],
     "source_code": "from django.http import HttpResponse\ndef index(request):\n    return HttpResponse('Hello, world.')\n"},
    {"package_name": "numpy", "registry": "pypi", "version": "1.26.0",
     "author": "NumPy Developers", "summary": "Array computing for Python",
     "requires_dist": [],
     "source_code": "import numpy as np\ndef compute(a, b):\n    return np.dot(a, b)\n"},
    {"package_name": "pandas", "registry": "pypi", "version": "2.1.3",
     "author": "The Pandas Development Team", "summary": "Data analysis toolkit",
     "requires_dist": ["numpy", "python-dateutil", "pytz", "tzdata"],
     "source_code": "import pandas as pd\ndef read(path):\n    return pd.read_csv(path)\n"},
    {"package_name": "scipy", "registry": "pypi", "version": "1.11.4",
     "author": "SciPy Developers", "summary": "Scientific computing library",
     "requires_dist": ["numpy"],
     "source_code": "from scipy import optimize\ndef minimize(func, x0):\n    return optimize.minimize(func, x0)\n"},
    {"package_name": "sqlalchemy", "registry": "pypi", "version": "2.0.23",
     "author": "Mike Bayer", "summary": "SQL toolkit and ORM",
     "requires_dist": ["typing-extensions"],
     "source_code": "from sqlalchemy import create_engine\ndef connect(url):\n    engine = create_engine(url)\n    return engine.connect()\n"},
    {"package_name": "celery", "registry": "pypi", "version": "5.3.6",
     "author": "Ask Solem", "summary": "Distributed task queue",
     "requires_dist": ["billiard", "kombu", "vine", "click-didyoumean"],
     "source_code": "from celery import Celery\napp = Celery('tasks', broker='redis://localhost')\n@app.task\ndef add(x, y):\n    return x + y\n"},
    {"package_name": "pytest", "registry": "pypi", "version": "7.4.3",
     "author": "Holger Krekel", "summary": "Python testing framework",
     "requires_dist": ["iniconfig", "packaging", "pluggy"],
     "source_code": "def test_addition():\n    assert 1 + 1 == 2\ndef test_string():\n    assert 'hello'.upper() == 'HELLO'\n"},
    {"package_name": "pydantic", "registry": "pypi", "version": "2.5.2",
     "author": "Samuel Colvin", "summary": "Data validation using Python type hints",
     "requires_dist": ["annotated-types", "pydantic-core", "typing-extensions"],
     "source_code": "from pydantic import BaseModel\nclass User(BaseModel):\n    name: str\n    age: int\n"},
    {"package_name": "fastapi", "registry": "pypi", "version": "0.104.1",
     "author": "Sebastian Ramirez", "summary": "Fast web framework for building APIs",
     "requires_dist": ["starlette", "pydantic", "anyio"],
     "source_code": "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/')\ndef read_root():\n    return {'message': 'Hello World'}\n"},
    {"package_name": "httpx", "registry": "pypi", "version": "0.25.2",
     "author": "Tom Christie", "summary": "HTTP client for Python",
     "requires_dist": ["certifi", "httpcore", "idna", "sniffio"],
     "source_code": "import httpx\ndef fetch(url):\n    response = httpx.get(url)\n    return response.json()\n"},
    {"package_name": "click", "registry": "pypi", "version": "8.1.7",
     "author": "Pallets", "summary": "Composable command line interface toolkit",
     "requires_dist": ["colorama"],
     "source_code": "import click\n@click.command()\n@click.option('--name', default='World')\ndef hello(name):\n    click.echo(f'Hello {name}!')\n"},
    {"package_name": "boto3", "registry": "pypi", "version": "1.33.0",
     "author": "Amazon Web Services", "summary": "AWS SDK for Python",
     "requires_dist": ["botocore", "jmespath", "s3transfer"],
     "source_code": "import boto3\ndef list_buckets():\n    s3 = boto3.client('s3')\n    return s3.list_buckets()\n"},
    {"package_name": "pillow", "registry": "pypi", "version": "10.1.0",
     "author": "Jeffrey A. Clark", "summary": "Python Imaging Library (Fork)",
     "requires_dist": [],
     "source_code": "from PIL import Image\ndef resize(path, size):\n    img = Image.open(path)\n    return img.resize(size)\n"},
    {"package_name": "matplotlib", "registry": "pypi", "version": "3.8.2",
     "author": "John D. Hunter", "summary": "Plotting library",
     "requires_dist": ["contourpy", "cycler", "fonttools", "kiwisolver", "numpy", "packaging", "pillow", "pyparsing", "python-dateutil"],
     "source_code": "import matplotlib.pyplot as plt\ndef plot(x, y):\n    plt.plot(x, y)\n    plt.show()\n"},
    {"package_name": "black", "registry": "pypi", "version": "23.12.0",
     "author": "Lukasz Langa", "summary": "Uncompromising Python code formatter",
     "requires_dist": ["click", "mypy-extensions", "packaging", "pathspec", "platformdirs"],
     "source_code": "import black\ndef format_code(source):\n    return black.format_str(source, mode=black.Mode())\n"},
    {"package_name": "uvicorn", "registry": "pypi", "version": "0.24.0",
     "author": "Tom Christie", "summary": "Lightning-fast ASGI server",
     "requires_dist": ["click", "h11"],
     "source_code": "import uvicorn\ndef serve(app, host='0.0.0.0', port=8000):\n    uvicorn.run(app, host=host, port=port)\n"},
    {"package_name": "gunicorn", "registry": "pypi", "version": "21.2.0",
     "author": "Benoit Chesneau", "summary": "WSGI HTTP Server for UNIX",
     "requires_dist": ["packaging"],
     "source_code": "import gunicorn\ndef run_server(app, bind='0.0.0.0:8000'):\n    options = {'bind': bind, 'workers': 4}\n"},
    {"package_name": "mypy", "registry": "pypi", "version": "1.7.1",
     "author": "Jukka Lehtosalo", "summary": "Optional static type checker",
     "requires_dist": ["mypy-extensions", "typing-extensions"],
     "source_code": "# mypy configuration\ndef check_types(filename):\n    from mypy import api\n    result = api.run([filename])\n    return result\n"},
    # --- npm packages ---
    {"package_name": "lodash", "registry": "npm", "version": "4.17.21",
     "author": "John-David Dalton", "summary": "JavaScript utility library",
     "dependencies": {"lodash.debounce": "^4.0.8"},
     "source_code": "function chunk(array, size) {\n  const result = [];\n  for (let i = 0; i < array.length; i += size) {\n    result.push(array.slice(i, i + size));\n  }\n  return result;\n}\nmodule.exports = { chunk };\n"},
    {"package_name": "express", "registry": "npm", "version": "4.18.2",
     "author": "TJ Holowaychuk", "summary": "Fast web framework for Node.js",
     "dependencies": {"body-parser": "1.20.1", "cookie": "0.5.0", "debug": "2.6.9"},
     "source_code": "const express = require('express');\nconst app = express();\napp.get('/', (req, res) => res.send('Hello World'));\napp.listen(3000);\n"},
    {"package_name": "react", "registry": "npm", "version": "18.2.0",
     "author": "Facebook", "summary": "JavaScript library for building user interfaces",
     "dependencies": {"loose-envify": "^1.1.0"},
     "source_code": "import React from 'react';\nfunction App() {\n  return <div>Hello World</div>;\n}\nexport default App;\n"},
    {"package_name": "axios", "registry": "npm", "version": "1.6.2",
     "author": "Matt Zabriskie", "summary": "Promise based HTTP client",
     "dependencies": {"follow-redirects": "^1.15.0", "form-data": "^4.0.0", "proxy-from-env": "^1.1.0"},
     "source_code": "const axios = require('axios');\nasync function fetchData(url) {\n  const response = await axios.get(url);\n  return response.data;\n}\n"},
    {"package_name": "chalk", "registry": "npm", "version": "5.3.0",
     "author": "Sindre Sorhus", "summary": "Terminal string styling",
     "dependencies": {},
     "source_code": "import chalk from 'chalk';\nconsole.log(chalk.blue('Hello world!'));\n"},
    {"package_name": "commander", "registry": "npm", "version": "11.1.0",
     "author": "TJ Holowaychuk", "summary": "Command-line interfaces",
     "dependencies": {},
     "source_code": "const { program } = require('commander');\nprogram.option('-d, --debug', 'output extra debugging');\nprogram.parse();\n"},
    {"package_name": "uuid", "registry": "npm", "version": "9.0.0",
     "author": "Robert Kieffer", "summary": "RFC4122 UUID generation",
     "dependencies": {},
     "source_code": "const { v4: uuidv4 } = require('uuid');\nfunction generateId() {\n  return uuidv4();\n}\n"},
    {"package_name": "dotenv", "registry": "npm", "version": "16.3.1",
     "author": "Scott Motte", "summary": "Loads environment variables from .env",
     "dependencies": {},
     "source_code": "require('dotenv').config();\nconst port = process.env.PORT || 3000;\n"},
    {"package_name": "typescript", "registry": "npm", "version": "5.3.2",
     "author": "Microsoft", "summary": "TypeScript language and compiler",
     "dependencies": {},
     "source_code": "interface User {\n  name: string;\n  age: number;\n}\nfunction greet(user: User): string {\n  return `Hello, ${user.name}`;\n}\n"},
    {"package_name": "webpack", "registry": "npm", "version": "5.89.0",
     "author": "Tobias Koppers", "summary": "Module bundler",
     "dependencies": {"acorn": "^8.7.1", "graceful-fs": "^4.2.9", "tapable": "^2.1.1"},
     "source_code": "const path = require('path');\nmodule.exports = {\n  entry: './src/index.js',\n  output: {\n    filename: 'bundle.js',\n    path: path.resolve(__dirname, 'dist'),\n  },\n};\n"},
]


def _generate_backstabbers(output_dir: Path, force: bool) -> list[dict]:
    """Generate malicious seed dataset."""
    sys.path.insert(0, str(PROJECT_ROOT))
    from data.datasets.download_backstabbers import download_backstabbers_dataset

    records = download_backstabbers_dataset(output_dir=str(output_dir), force=force)
    print(f"  {len(records)} malicious records -> backstabbers_seed.json")
    return records


def _generate_benign(output_dir: Path, force: bool) -> list[dict]:
    """Generate synthetic benign dataset without network access."""
    output_file = output_dir / "benign_sample.json"
    if output_file.exists() and not force:
        print(f"  benign_sample.json already exists, skipping")
        with open(output_file, "r", encoding="utf-8") as f:
            return json.load(f)

    collected_at = datetime.now(timezone.utc).isoformat()
    records = []
    seen: set[tuple[str, str]] = set()

    for entry in SYNTHETIC_BENIGN:
        key = (entry["package_name"], entry["registry"])
        if key in seen:
            continue
        seen.add(key)
        records.append({
            "package_name": entry["package_name"],
            "registry": entry["registry"],
            "label": "benign",
            "version": entry.get("version", ""),
            "author": entry.get("author", ""),
            "summary": entry.get("summary", ""),
            "source_code": entry.get("source_code", ""),
            "requires_dist": entry.get("requires_dist", []),
            "dependencies": entry.get("dependencies", {}),
            "source": "synthetic_benign",
            "collected_at": collected_at,
        })

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    print(f"  {len(records)} benign records -> benign_sample.json")
    return records


def _generate_real_benign(output_dir: Path, count: int, force: bool) -> list[dict]:
    """Fetch real benign package metadata from PyPI and npm (requires network)."""
    sys.path.insert(0, str(PROJECT_ROOT))
    from data.datasets.build_legit_dataset import build_legit_dataset

    records = build_legit_dataset(
        output_dir=str(output_dir),
        count=count,
        registry="both",
        force=force,
    )
    print(f"  {len(records)} real benign records -> benign_dataset.json")
    return records


def _normalize(output_dir: Path, real_mode: bool = False) -> None:
    """Normalize both datasets."""
    sys.path.insert(0, str(PROJECT_ROOT))
    from data.datasets.normalize_records import normalize_dataset

    mal_in = output_dir / "backstabbers_seed.json"
    # In real mode, benign data comes from build_legit_dataset -> benign_dataset.json
    # In synthetic mode, it comes from the built-in records -> benign_sample.json
    if real_mode:
        ben_in = output_dir / "benign_dataset.json"
        if not ben_in.exists():
            ben_in = output_dir / "benign_sample.json"
    else:
        ben_in = output_dir / "benign_sample.json"

    if mal_in.exists():
        normalize_dataset(str(mal_in), str(output_dir / "malicious_normalized.json"))
    if ben_in.exists():
        normalize_dataset(str(ben_in), str(output_dir / "benign_normalized.json"))
    print("  Normalization complete")


def _split(output_dir: Path, force: bool) -> None:
    """Label and split into train/val/test."""
    sys.path.insert(0, str(PROJECT_ROOT))
    from data.datasets.label_and_split import label_and_split

    splits_dir = str(output_dir / "splits")
    stats = label_and_split(
        malicious_path=str(output_dir / "malicious_normalized.json"),
        benign_path=str(output_dir / "benign_normalized.json"),
        output_dir=splits_dir,
        seed=42,
        force=force,
    )
    print(f"  Split stats: {json.dumps(stats, indent=2)}")


def _train_xgboost() -> None:
    """Train XGBoost classifier."""
    sys.path.insert(0, str(PROJECT_ROOT))
    from ml.train_classifier import train_and_save

    train_and_save()
    print("  XGBoost training complete")


def _build_faiss() -> None:
    """Build FAISS index from benign dataset."""
    sys.path.insert(0, str(PROJECT_ROOT))
    from ml.build_faiss_index import build

    build()
    print("  FAISS index build complete")


def generate_all(force: bool = False, real: bool = False, count: int = 200) -> None:
    """Run the full data pipeline end-to-end.

    Args:
        force: Overwrite existing files.
        real: If True, fetch live data from PyPI/npm (requires network).
              If False, use built-in synthetic records (offline, fast).
        count: Number of packages per registry when using --real mode.
    """
    mode_label = "REAL DATA (network required)" if real else "SYNTHETIC (offline)"
    print("=" * 60)
    print(f"Supply Chain Detector — Full Data Pipeline [{mode_label}]")
    print("=" * 60)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("\n[1/6] Generating malicious seed...")
    _generate_backstabbers(PROCESSED_DIR, force)

    if real:
        print(f"\n[2/6] Fetching {count} real benign packages per registry...")
        _generate_real_benign(PROCESSED_DIR, count, force)
    else:
        print("\n[2/6] Generating synthetic benign dataset...")
        _generate_benign(PROCESSED_DIR, force)

    print("\n[3/6] Normalizing datasets...")
    _normalize(PROCESSED_DIR, real_mode=real)

    print("\n[4/6] Splitting into train/val/test...")
    _split(PROCESSED_DIR, force)

    print("\n[5/6] Training XGBoost classifier...")
    _train_xgboost()

    print("\n[6/6] Building FAISS index...")
    _build_faiss()

    print("\n" + "=" * 60)
    print("Full data pipeline completed successfully!")
    artifacts = list(PROCESSED_DIR.rglob("*"))
    files = [f for f in artifacts if f.is_file()]
    print(f"  Generated {len(files)} files in data/processed/")
    for f in sorted(files):
        size_kb = f.stat().st_size / 1024
        print(f"    {f.relative_to(PROJECT_ROOT)} ({size_kb:.1f} KB)")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate all datasets, train model, build FAISS")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument("--real", action="store_true",
                        help="Fetch real data from PyPI/npm (requires network). "
                             "Without this flag, uses fast synthetic data.")
    parser.add_argument("--count", type=int, default=200,
                        help="Packages per registry in --real mode (default: 200)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    generate_all(force=args.force, real=args.real, count=args.count)

