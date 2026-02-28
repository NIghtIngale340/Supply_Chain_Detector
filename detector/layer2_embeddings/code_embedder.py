import numpy as np
from sentence_transformers import SentenceTransformer

_MODEL_NAME = "all-MiniLM-L6-v2"
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def _normalize_source(source_code: str) -> str:
    MAX_CHARS = 10000
    text = source_code.strip()
    text = " ".join(text.split())
    return text[:MAX_CHARS]


def encode(source_code: str) -> np.ndarray:
    if not source_code or not source_code.strip():
        model = _get_model()
        dim = model.get_sentence_embedding_dimension()
        return np.zeros((dim,), dtype=np.float32)

    text = _normalize_source(source_code)
    model = _get_model()
    embedding = model.encode(text, show_progress_bar=False, convert_to_numpy=True)

    if embedding.ndim > 1:
        embedding = embedding.flatten()

    return embedding


def get_embedding_dim() -> int:
    model = _get_model()
    return model.get_sentence_embedding_dimension()
