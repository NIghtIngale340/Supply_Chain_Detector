import sys
import json
import faiss
import numpy as np
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from detector.layer2_embeddings.code_embedder import encode as embed_code  # noqa: E402
BENIGN_DATA_PATH = _PROJECT_ROOT / "data" / "processed" / "benign_normalized.json"
INDEX_DIR = _PROJECT_ROOT / "data" / "processed"
INDEX_FILE = INDEX_DIR / "faiss.index"
MAPPING_FILE = INDEX_DIR / "faiss_id_mapping.json"


def _load_benign_records() -> list[dict]:
    if not BENIGN_DATA_PATH.exists():
        raise FileNotFoundError(f"Benign dataset not found: {BENIGN_DATA_PATH}")
    with open(BENIGN_DATA_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)
    print(f"Loaded {len(records)} benign records")
    return records


def _embed_records(records: list[dict]) -> tuple[np.ndarray, list[dict]]:
    embeddings = []
    id_mapping = []
    skipped = 0
    for i, record in enumerate(records):
        source = (
            record.get("source_code", "")
            or record.get("source", "")
            or record.get("package_name", "")
            or record.get("name", "")
        )
        if not source or not source.strip():
            skipped += 1
            continue
        try:
            vec = embed_code(source)
            embeddings.append(vec)
            package_name = record.get("package_name") or record.get("name") or f"record_{i}"
            id_mapping.append(
                {
                    "index": len(id_mapping),
                    "name": package_name,
                    "registry": record.get("registry", "unknown"),
                }
            )
        except Exception as e:
            print(f"  ⚠ Skipping record {i}: {e}")
            skipped += 1
    print(f"Embedded {len(embeddings)} records, skipped {skipped}")
    if not embeddings:
        raise ValueError("No valid embeddings produced")
    matrix = np.vstack(embeddings).astype(np.float32)
    return matrix, id_mapping


def _build_index(embeddings: np.ndarray) -> faiss.IndexFlatL2:
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    print(f"Built FAISS index: {index.ntotal} vectors, dim={dim}")
    return index


def _save_index(index: faiss.IndexFlatL2, id_mapping: list[dict]) -> None:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_FILE))
    with open(MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(id_mapping, f, indent=2)
    print(f"Saved index → {INDEX_FILE}")
    print(f"Saved mapping → {MAPPING_FILE}")


def build() -> None:
    print("=" * 50)
    print("Building FAISS index from benign dataset")
    print("=" * 50)
    records = _load_benign_records()
    embeddings, id_mapping = _embed_records(records)
    index = _build_index(embeddings)
    _save_index(index, id_mapping)
    print("FAISS index build complete!")


if __name__ == "__main__":
    build()
