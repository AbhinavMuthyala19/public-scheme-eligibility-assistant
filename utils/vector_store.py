"""Singletons and helpers for the ChromaDB-backed scheme vector store."""

from __future__ import annotations

from functools import lru_cache

import chromadb
from chromadb.api.models.Collection import Collection
from sentence_transformers import SentenceTransformer

from config import CHROMA_DB_PATH, COLLECTION_NAME, EMBEDDING_MODEL


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL)


@lru_cache(maxsize=1)
def get_collection() -> Collection:
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    return client.get_collection(COLLECTION_NAME)


def embed_text(text: str) -> list[float]:
    return get_embedding_model().encode(text).tolist()


def query_schemes(query_text: str, n_results: int) -> dict:
    """Run a semantic search against the scheme collection.

    Returns the raw ChromaDB query result (ids, documents, metadatas, distances).
    """
    collection = get_collection()
    n_results = max(1, min(n_results, collection.count()))

    return collection.query(
        query_embeddings=[embed_text(query_text)],
        n_results=n_results,
    )
