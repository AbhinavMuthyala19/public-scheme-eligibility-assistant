"""Chroma client factory: hosted Chroma Cloud when credentials are set,
otherwise a local persistent DB for offline development."""

import chromadb

from config import (
    CHROMA_API_KEY, CHROMA_TENANT, CHROMA_DATABASE,
    CHROMA_DB_PATH, COLLECTION_NAME, COLLECTION_METADATA,
)


def get_client():
    if CHROMA_API_KEY:
        return chromadb.CloudClient(
            api_key=CHROMA_API_KEY,
            tenant=CHROMA_TENANT,
            database=CHROMA_DATABASE,
        )
    return chromadb.PersistentClient(path=CHROMA_DB_PATH)


def get_collection(create: bool = False):
    """Return the schemes collection. With create=True, rebuild it fresh."""
    client = get_client()
    if create:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        return client.get_or_create_collection(
            name=COLLECTION_NAME, metadata=COLLECTION_METADATA
        )
    return client.get_collection(COLLECTION_NAME)
