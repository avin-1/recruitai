from typing import Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from numpy.linalg import norm


_model: Optional[SentenceTransformer] = None


def _get_model(name: str) -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(name)
    return _model


def get_embedding(text: str, model_name: str) -> np.ndarray:
    model = _get_model(model_name)
    emb = model.encode([text], convert_to_numpy=True)[0]
    return emb


def semantic_match(resume_text: str, job_text: str, model_name: str) -> float:
    a = get_embedding(resume_text, model_name)
    b = get_embedding(job_text, model_name)
    sim = float(np.dot(a, b) / (norm(a) * norm(b) + 1e-8))
    # map cosine [-1,1] to [0,1]
    return (sim + 1.0) / 2.0


