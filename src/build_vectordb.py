"""Builds (or rebuilds) the Chroma vector store from data/merged_schemes.csv.

Run once from the project root:

    python src/build_vectordb.py
"""

import sys
from pathlib import Path

import chromadb
import pandas as pd
from sentence_transformers import SentenceTransformer

# Allow running as `python src/build_vectordb.py` from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (  # noqa: E402
    CHROMA_DB_PATH,
    COLLECTION_METADATA,
    COLLECTION_NAME,
    DATA_PATH,
    EMBEDDING_MODEL,
)

BATCH_SIZE = 128


def main() -> None:
    print(f"Loading data from {DATA_PATH} ...")
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} rows.")

    print(f"Loading embedding model '{EMBEDDING_MODEL}' ...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata=COLLECTION_METADATA,
    )

    documents = df["document"].astype(str).tolist()
    ids = [str(i) for i in df.index]
    metadatas = [
        {
            "slug": str(row.slug),
            "scheme_name": str(row.scheme_name),
            "state": str(row.state),
            "level": str(row.level),
            "categories": str(row.categories),
            "ministry": str(row.ministry),
        }
        for row in df.itertuples()
    ]

    for start in range(0, len(documents), BATCH_SIZE):
        end = start + BATCH_SIZE
        batch_docs = documents[start:end]

        embeddings = model.encode(batch_docs, show_progress_bar=False).tolist()

        collection.add(
            ids=ids[start:end],
            documents=batch_docs,
            embeddings=embeddings,
            metadatas=metadatas[start:end],
        )

        print(f"{min(end, len(documents))}/{len(documents)} inserted...")

    print("Documents in DB:", collection.count())


if __name__ == "__main__":
    main()
