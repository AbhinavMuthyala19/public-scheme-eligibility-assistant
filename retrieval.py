"""Vector retrieval over the Chroma scheme index.

Loads the embedding model + Chroma collection once, and searches by
embedding a query, over-fetching chunks, then collapsing them back to
unique schemes (since each scheme was split into several chunks).
"""

import chromadb
from sentence_transformers import SentenceTransformer

from config import CHROMA_DB_PATH, COLLECTION_NAME, EMBEDDING_MODEL, TOP_K


class SchemeRetriever:
    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        self.collection = self.client.get_collection(COLLECTION_NAME)

    def search_schemes(self, query_text: str, top_k: int = TOP_K,
                       over_fetch: int = 4, where: dict = None):
        """Return up to top_k unique schemes ranked by best-chunk similarity.

        `where` is an optional Chroma metadata filter, e.g.
        {"state": {"$in": ["Punjab", "All"]}} to keep only a user's own
        state plus nationally-available schemes.
        """
        query_embedding = self.model.encode(query_text).tolist()

        query_args = {
            "query_embeddings": [query_embedding],
            "n_results": top_k * over_fetch,   # fetch extra chunks, then dedupe
        }
        if where:
            query_args["where"] = where

        results = self.collection.query(**query_args)

        metadatas = results["metadatas"][0]
        distances = results["distances"][0]
        documents = results["documents"][0]

        # Collapse chunks -> schemes, keeping each scheme's closest chunk.
        best = {}
        for meta, distance, document in zip(metadatas, distances, documents):
            scheme_id = meta["scheme_id"]
            if scheme_id not in best or distance < best[scheme_id]["distance"]:
                best[scheme_id] = {
                    "scheme_id": scheme_id,
                    "slug": meta.get("slug"),
                    "scheme_name": meta.get("scheme_name"),
                    "state": meta.get("state"),
                    "level": meta.get("level"),
                    "categories": meta.get("categories"),
                    "ministry": meta.get("ministry"),
                    "distance": float(distance),
                    "best_chunk": document,
                }

        ranked = sorted(best.values(), key=lambda s: s["distance"])
        return ranked[:top_k]
