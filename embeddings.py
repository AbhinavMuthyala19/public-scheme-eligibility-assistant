"""Text embeddings via the OpenAI API.

Replaces the local sentence-transformers model so the app needs no torch —
much lighter to deploy. Used by both the vector-DB build and query-time search.
"""

from openai import OpenAI

from config import OPENAI_API_KEY, EMBEDDING_MODEL_OPENAI

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def embed_texts(texts, batch_size=100):
    """Embed a list of strings, batching requests to the API."""
    client = _get_client()
    vectors = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        resp = client.embeddings.create(model=EMBEDDING_MODEL_OPENAI, input=batch)
        vectors.extend(d.embedding for d in resp.data)
    return vectors


def embed_query(text):
    """Embed a single query string."""
    return embed_texts([text])[0]
