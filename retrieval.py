"""Vector retrieval over the scheme index (Chroma Cloud or local).

Embeds the query via the OpenAI API, over-fetches chunks, then collapses
them back to unique schemes (each scheme was split into several chunks).
"""

from config import TOP_K
from embeddings import embed_query
from vectorstore import get_collection


class SchemeRetriever:
    def __init__(self):
        self.collection = get_collection()

    def search_schemes(self, query_text: str, top_k: int = TOP_K,
                       over_fetch: int = 4, where: dict = None):
        """Return up to top_k unique schemes ranked by best-chunk similarity.

        `where` is an optional Chroma metadata filter, e.g.
        {"state": {"$in": ["Punjab", "All"]}}.
        """
        query_embedding = embed_query(query_text)

        query_args = {
            "query_embeddings": [query_embedding],
            "n_results": top_k * over_fetch,
        }
        if where:
            query_args["where"] = where

        results = self.collection.query(**query_args)

        metadatas = results["metadatas"][0]
        distances = results["distances"][0]
        documents = results["documents"][0]

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
