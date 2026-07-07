import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer

df = pd.read_csv("data/merged_schemes.csv")

print("Loading model...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("Model loaded.")

client = chromadb.PersistentClient(
    path="./chroma_db"
)

try:
    client.delete_collection(
        "government_schemes"
    )
except:
    pass

collection = client.get_or_create_collection(
    name="government_schemes"
)

for index, row in df.iterrows():

    document = row["document"]

    embedding = model.encode(
        document
    ).tolist()

    metadata = {
        "slug": str(row["slug"]),
        "scheme_name": str(row["scheme_name"]),
        "state": str(row["state"]),
        "level": str(row["level"]),
        "categories": str(row["categories"]),
        "ministry": str(row["ministry"])
    }

    collection.add(
        ids=[str(index)],
        documents=[document],
        embeddings=[embedding],
        metadatas=[metadata]
    )

    if (index + 1) % 100 == 0:
        print(f"{index + 1} inserted...")

print(
    "Documents in DB:",
    collection.count()
)