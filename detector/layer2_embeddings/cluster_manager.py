import json
import numpy as np
import faiss
from pathlib import Path




_PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
INDEX_FILE = _PROJECT_ROOT / "data" / "processed" / "faiss.index"
MAPPING_FILE = _PROJECT_ROOT / "data" / "processed" / "faiss_id_mapping.json"
_index = None
_mapping = None



def _load_index():
    global _index, _mapping
    if _index is not None and _mapping is not None:
        return _index, _mapping
    if not INDEX_FILE.exists():
        raise FileNotFoundError(f"FAISS index not found: {INDEX_FILE}")
    _index = faiss.read_index(str(INDEX_FILE))
    if MAPPING_FILE.exists():
        with open(MAPPING_FILE, "r", encoding="utf-8") as f:
            _mapping = json.load(f)
    else:
        _mapping = []
    print(f"Loaded FAISS index: {_index.ntotal} vectors")
    return _index, _mapping


def find_nearest(embedding, k=5):
    index, mapping = _load_index()
    query = embedding.reshape(1, -1).astype(np.float32)
    distances, indices = index.search(query, k)
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        pkg_info = {}
        if idx < len(mapping):
            pkg_info = mapping[idx]
        results.append({"distance": float(dist), "index": int(idx), "name": pkg_info.get("name", f"id_{idx}"), "registry": pkg_info.get("registry", "unknown")})
    return results



def distance_to_nearest(embedding: np.ndarray):
    results = find_nearest(embedding, k=1)
    if not results:
        return float("inf")
    return results[0]["distance"]