"""RailNiyam semantic embedding and search module.
Supports:
1. Google Gemini Embeddings (text-embedding-004) when GEMINI_API_KEY is available.
2. Local dense semantic embeddings via normalized TF-IDF + Latent Semantic projection (scikit-learn)
   ensuring 100% offline functionality without external network or download dependencies.
3. Chroma-compatible EmbeddingFunction subclass for Chroma persistent collections.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import requests
from chromadb.api.types import EmbeddingFunction
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from app.chunking import Chunk, get_all_chunks

# Read .env if present
ENV_FILE = ROOT / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


class LocalSemanticEmbedder:
    """Offline semantic vectorizer using fitted TF-IDF + LSA projection."""

    def __init__(self, corpus: list[str] | None = None, dim: int = 64):
        self.dim = dim
        if corpus is None:
            corpus = [c.text for c in get_all_chunks()]
        # Supplement corpus with typical domain search phrases
        domain_seeds = [
            "cancellation charge confirmed ticket 48 hours",
            "tatkal ticket refund rules sleeper ac",
            "train cancelled e-ticket refund without tdr",
            "train late more than 3 hours full refund",
            "ac failure tdr difference of fare tte certificate",
            "clerkage charge second class rac waitlisted",
            "unreserved ticket cancellation clerkage",
            "partially confirmed ticket cancel chart preparation",
        ]
        full_corpus = list(corpus) + domain_seeds
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        tfidf_mat = self.vectorizer.fit_transform(full_corpus)
        n_components = min(self.dim, tfidf_mat.shape[1] - 1, tfidf_mat.shape[0] - 1)
        self.svd = TruncatedSVD(n_components=max(4, n_components), random_state=42)
        self.svd.fit(tfidf_mat)

    def embed(self, texts: list[str]) -> list[list[float]]:
        tfidf_mat = self.vectorizer.transform(texts)
        dense = self.svd.transform(tfidf_mat)
        norms = np.linalg.norm(dense, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized = (dense / norms).astype(float)
        return normalized.tolist()


def _embed_gemini(texts: list[str], api_key: str) -> list[list[float]] | None:
    """Call Google Gemini batchEmbedContents endpoint."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:batchEmbedContents?key={api_key}"
    requests_payload = [
        {"model": "models/text-embedding-004", "content": {"parts": [{"text": t[:1000]}]}}
        for t in texts
    ]
    try:
        resp = requests.post(url, json={"requests": requests_payload}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        embeddings = [item["values"] for item in data.get("embeddings", [])]
        if len(embeddings) == len(texts):
            return embeddings
    except Exception:
        pass
    return None


class RailNiyamEmbeddingFunction(EmbeddingFunction):
    """Chroma-compatible embedding function supporting Gemini with local offline fallback."""

    def __init__(self, corpus: list[str] | None = None):
        super().__init__()
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.local_embedder = LocalSemanticEmbedder(corpus=corpus)

    def __call__(self, input: list[str]) -> list[list[float]]:
        return self.embed_documents(input)

    def embed_documents(self, input: list[str]) -> list[list[float]]:
        if self.gemini_key:
            res = _embed_gemini(input, self.gemini_key)
            if res:
                return res
        return self.local_embedder.embed(input)

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self.embed_documents(input)


_DEFAULT_EMBEDDER = RailNiyamEmbeddingFunction()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Compute embeddings for a list of strings."""
    return _DEFAULT_EMBEDDER.embed_documents(texts)


def semantic_search(query: str, chunks: list[Chunk] | None = None, top_k: int = 3) -> list[dict]:
    """Perform cosine-similarity semantic search across chunks."""
    if chunks is None:
        chunks = get_all_chunks()

    chunk_texts = [c.text for c in chunks]
    chunk_vectors = np.array(_DEFAULT_EMBEDDER.embed_documents(chunk_texts))
    query_vector = np.array(_DEFAULT_EMBEDDER.embed_query([query]))[0]

    # Cosine similarities
    dot_products = np.dot(chunk_vectors, query_vector)
    top_indices = np.argsort(dot_products)[::-1][:top_k]

    results = []
    for idx in top_indices:
        c = chunks[idx]
        score = float(dot_products[idx])
        results.append({
            "chunk_id": c.chunk_id,
            "title": c.title,
            "source": c.source,
            "page": c.page,
            "score": round(score, 4),
            "text": c.text,
        })
    return results


if __name__ == "__main__":
    test_q = "How much is deducted for cancelling 3AC ticket 2 days early?"
    hits = semantic_search(test_q, top_k=3)
    print(f"Query: {test_q}\n")
    for h in hits:
        print(f"[{h['chunk_id']}] (Score: {h['score']:.4f}) {h['title']} (Source: {h['source']}, Page: {h['page']})")
