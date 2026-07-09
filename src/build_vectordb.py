import os
import sys

# Make the project root importable so "from config import ..." works
# when this script is run as "python3 src/build_vectordb.py".
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer

from config import (
    DATA_PATH,
    CHROMA_DB_PATH,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    COLLECTION_METADATA,
)

# ==========================
# Chunking config
# ==========================
# all-MiniLM-L6-v2 only reads ~256 tokens, so we split long scheme
# documents into overlapping word-windows. Overlap keeps information that
# sits on a boundary from being lost between two chunks.
CHUNK_SIZE = 180      # words per chunk (stays under the model's token limit)
CHUNK_OVERLAP = 40    # words shared between consecutive chunks
EMBED_BATCH = 64      # chunks embedded per batch


def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping word windows."""
    words = text.split()
    if not words:
        return []

    step = max(1, size - overlap)
    chunks = []
    for start in range(0, len(words), step):
        chunks.append(" ".join(words[start:start + size]))
        if start + size >= len(words):
            break
    return chunks


def main():
    df = pd.read_csv(DATA_PATH)

    print("Loading embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("Model loaded.")

    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    # Rebuild from scratch each run.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata=COLLECTION_METADATA,
    )

    # 1) Build every chunk + its metadata (linked back to the scheme).
    ids, documents, metadatas = [], [], []

    for index, row in df.iterrows():
        document = str(row["document"])

        for chunk_index, chunk in enumerate(chunk_text(document)):
            ids.append(f"{index}_{chunk_index}")
            documents.append(chunk)
            metadatas.append({
                "scheme_id": str(index),
                "chunk_index": chunk_index,
                "slug": str(row["slug"]),
                "scheme_name": str(row["scheme_name"]),
                "state": str(row["state"]),
                "level": str(row["level"]),
                "categories": str(row["categories"]),
                "ministry": str(row["ministry"]),
            })

    print(f"{len(df)} schemes -> {len(documents)} overlapping chunks")

    # 2) Embed all chunks in batches (far faster than one-by-one).
    print("Embedding chunks...")
    embeddings = model.encode(
        documents,
        batch_size=EMBED_BATCH,
        show_progress_bar=True,
    ).tolist()

    # 3) Write to Chroma in batches.
    print("Writing to Chroma...")
    add_batch = 1000
    for i in range(0, len(documents), add_batch):
        collection.add(
            ids=ids[i:i + add_batch],
            documents=documents[i:i + add_batch],
            embeddings=embeddings[i:i + add_batch],
            metadatas=metadatas[i:i + add_batch],
        )
        print(f"  inserted {min(i + add_batch, len(documents))}/{len(documents)}")

    print("Chunks in DB:", collection.count())


if __name__ == "__main__":
    main()
