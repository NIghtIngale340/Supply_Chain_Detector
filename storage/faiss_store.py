from __future__ import annotations

from pathlib import Path


class FaissStore:
    def __init__(self, index_path: str | Path) -> None:
        self.index_path = Path(index_path)

    def exists(self) -> bool:
        return self.index_path.exists()

    def save(self, index) -> None:
        import faiss

        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(self.index_path))

    def load(self):
        import faiss

        if not self.exists():
            raise FileNotFoundError(f"FAISS index not found at {self.index_path}")
        return faiss.read_index(str(self.index_path))
