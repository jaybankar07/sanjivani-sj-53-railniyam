"""Chroma persistent vectorstore for RailNiyam chunks.
Indexes all chunks with metadata (source, page, title) into a persistent Chroma collection.
Provides semantic search querying the persistent collection.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import chromadb
from app.chunking import get_all_chunks, Chunk
from app.embed import RailNiyamEmbeddingFunction

CHROMA_DIR = ROOT / "data" / "chroma_db"
COLLECTION_NAME = "railniyam_chunks"


def get_client():
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def get_collection(client=None):
    if client is None:
        client = get_client()
    embedding_fn = RailNiyamEmbeddingFunction()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"description": "RailNiyam refund and cancellation rule chunks"}
    )


def index_chunks(force: bool = False) -> int:
    """Index all chunks into the persistent Chroma collection."""
    collection = get_collection()
    current_count = collection.count()
    if current_count > 0 and not force:
        return current_count

    chunks = get_all_chunks()
    ids = [c.chunk_id for c in chunks]
    documents = [c.text for c in chunks]
    metadatas = [
        {"title": c.title, "source": c.source, "page": int(c.page)}
        for c in chunks
    ]

    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    return collection.count()


def search_semantic(query: str, top_k: int = 5) -> list[dict]:
    """Semantic search against the persistent Chroma collection."""
    collection = get_collection()
    if collection.count() == 0:
        index_chunks()

    res = collection.query(query_texts=[query], n_results=top_k)

    hits = []
    if res and res.get("ids") and len(res["ids"][0]) > 0:
        ids = res["ids"][0]
        docs = res["documents"][0] if res.get("documents") else [""] * len(ids)
        metas = res["metadatas"][0] if res.get("metadatas") else [{}] * len(ids)
        dists = res["distances"][0] if res.get("distances") else [0.0] * len(ids)

        for cid, doc, meta, dist in zip(ids, docs, metas, dists):
            # Chroma distances: lower distance means higher similarity
            sim_score = round(max(0.0, 1.0 - (dist / 2.0)), 4)
            hits.append({
                "chunk_id": cid,
                "title": meta.get("title", ""),
                "source": meta.get("source", ""),
                "page": meta.get("page", 1),
                "distance": round(dist, 4),
                "score": sim_score,
                "text": doc,
            })
    return hits


if __name__ == "__main__":
    count = index_chunks(force=True)
    print(f"Indexed {count} chunks into persistent Chroma collection at: {CHROMA_DIR}")

    sample_query = "What happens if train is late by 3 hours?"
    results = search_semantic(sample_query, top_k=3)
    print(f"\nSemantic query: '{sample_query}'")
    for r in results:
        print(f"- [{r['chunk_id']}] (Score: {r['score']:.4f}) {r['title']} | Source: {r['source']} (Page {r['page']})")
