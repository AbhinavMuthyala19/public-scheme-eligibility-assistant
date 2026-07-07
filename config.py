# ==========================
# Paths
# ==========================

CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "government_schemes"

DATA_PATH = "./data/merged_schemes.csv"

# ==========================
# Embedding Model
# ==========================

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ==========================
# Ollama
# ==========================

OLLAMA_MODEL = "llama3.2"

# Examples:
# "llama3.2"
# "qwen3"
# "gemma3"
# "mistral"

# ==========================
# Retrieval
# ==========================

TOP_K = 10

# ==========================
# Chroma Collection
# ==========================

COLLECTION_METADATA = {
    "description": "Government Scheme Eligibility Assistant"
}