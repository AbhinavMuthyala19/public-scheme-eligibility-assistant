# ==========================
# Environment variables
# ==========================

import os
from dotenv import load_dotenv

load_dotenv()  # reads .env into environment variables

# ==========================
# Paths
# ==========================

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
COLLECTION_NAME = "government_schemes"

DATA_PATH = "./data/merged_schemes.csv"

# ==========================
# Chroma Cloud (set these to use hosted Chroma instead of a local DB)
# ==========================

CHROMA_API_KEY = os.getenv("CHROMA_API_KEY")
CHROMA_TENANT = os.getenv("CHROMA_TENANT")
CHROMA_DATABASE = os.getenv("CHROMA_DATABASE")

# ==========================
# Embedding Model
# ==========================

# Local model (legacy / offline use)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Hosted embeddings via OpenAI — used everywhere now (no torch needed).
EMBEDDING_MODEL_OPENAI = "text-embedding-3-small"

# ==========================
# Ollama  (commented out — replaced by hosted LLM providers)
# ==========================

# OLLAMA_MODEL = "llama3.2"

# Examples:
# "llama3.2"
# "qwen3"
# "gemma3"
# "mistral"

# ==========================
# LLM Providers (Claude + GPT)
# ==========================

# Anthropic (Claude)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
# Alternatives: "claude-sonnet-4-6" (stronger reasoning, higher cost)

# OpenAI (GPT)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"
# Alternatives: "gpt-4o" (stronger, higher cost)

# Which providers the ensemble runs and compares.
ENSEMBLE_PROVIDERS = ["claude", "openai"]

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
