import os
import sys

# Make the project root importable when run as "python3 src/build_vectordb.py".
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from config import DATA_PATH
from embeddings import embed_texts
from vectorstore import get_collection

# ==========================
# Chunking config
# ==========================
CHUNK_SIZE = 180      # words per chunk
CHUNK_OVERLAP = 40    # words shared between consecutive chunks
ADD_BATCH = 250       # rows written per batch (Chroma Cloud free-tier write cap)


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

    # Rebuild the collection fresh (Chroma Cloud if configured, else local).
    collection = get_collection(create=True)

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

    total = len(documents)
    print(f"{len(df)} schemes -> {total} overlapping chunks")
    print("Embedding + uploading in batches...")

    for i in range(0, total, ADD_BATCH):
        batch_docs = documents[i:i + ADD_BATCH]
        batch_emb = embed_texts(batch_docs)
        collection.add(
            ids=ids[i:i + ADD_BATCH],
            documents=batch_docs,
            embeddings=batch_emb,
            metadatas=metadatas[i:i + ADD_BATCH],
        )
        print(f"  uploaded {min(i + ADD_BATCH, total)}/{total}")

    print("Chunks in DB:", collection.count())


if __name__ == "__main__":
    main()
