# Public Scheme Eligibility Assistant

An Agentic AI application that recommends Indian Government schemes based on a user's profile using Retrieval-Augmented Generation (RAG), ChromaDB, and multiple AI agents.

---

# Tech Stack

- Python
- ChromaDB
- Sentence Transformers
- Ollama
- Streamlit
- Pydantic
- Pytest

---

# Project Architecture

```
User
    │
    ▼
Orchestration Agent
    │
    ▼
Profile Agent  ───────────►  extracts a structured profile from free text,
    │                        asking follow-up questions until required
    │                        fields (age, gender, state) are known
    ▼
Search Agent   ───────────►  semantic search over ChromaDB, re-ranked with
    │                        a state-relevance boost
    ▼
Eligibility Agent ────────►  judges each candidate scheme against the
    │                        profile: eligible / likely_eligible /
    │                        not_eligible / insufficient_info
    ▼
Explanation Agent ────────►  turns the verdict into a short, plain-language
    │                        explanation for the user
    ▼
Action Agent   ───────────►  summarizes the application process into
                             concrete steps and extracts the apply link
```

The Orchestration Agent is the only entry point: it routes each user message
through the Profile Agent first, and once the profile has enough information,
runs Search → Eligibility → Explanation → Action to build the final
recommendations shown in the Streamlit UI.

---

# Folder Structure

```
SchemesProject/
│
├── agents/
│   ├── orchestrator.py        # Orchestration Agent
│   ├── profile_agent.py       # Profile Agent
│   ├── search_agent.py        # Search Agent
│   ├── eligibility_agent.py   # Eligibility Agent
│   ├── explanation_agent.py   # Explanation Agent
│   └── action_agent.py        # Action Agent
│
├── chroma_db/                 # generated locally, not committed
│
├── data/
│   └── merged_schemes.csv
│
├── models/
│   └── schemas.py             # Pydantic schemas shared by every agent
│
├── prompts/
│   ├── profile_prompt.py
│   ├── eligibility_prompt.py
│   ├── explanation_prompt.py
│   └── action_prompt.py
│
├── src/
│   └── build_vectordb.py      # one-off script to (re)build the vector DB
│
├── tests/                     # pytest suite (unit + one integration test)
│
├── utils/
│   ├── ollama_client.py       # structured (schema-validated) Ollama calls
│   ├── vector_store.py        # ChromaDB + embedding model singletons
│   └── formatting.py          # prompt text helpers
│
├── app.py                     # Streamlit chat UI
├── config.py
├── requirements.txt
├── pytest.ini
├── README.md
└── .gitignore
```

---

# Setup Instructions

## 1. Clone the repository

```bash
git clone <repository-url>
```

Move into the project.

```bash
cd SchemesProject
```

---

## 2. Create Virtual Environment

Windows

```bash
python -m venv schemesproject
```

Activate

PowerShell

```powershell
.\schemesproject\Scripts\Activate.ps1
```

Command Prompt

```cmd
schemesproject\Scripts\activate.bat
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Install Ollama

Download and install Ollama.

https://ollama.com

Pull the required model.

Example:

```bash
ollama pull llama3.2
```

Ensure Ollama is running before starting the application.

---

## 5. Prepare the Data

Place the dataset inside:

```
data/
```

Expected file:

```
merged_schemes.csv
```

---

## 6. Build the Vector Database

Run:

```bash
python src/build_vectordb.py
```

This creates:

```
chroma_db/
```

The vector database only needs to be built once. Re-run the script whenever
`data/merged_schemes.csv` changes.

---

# Running the Application

Make sure Ollama is running (`ollama serve` or the desktop app), then run Streamlit.

```bash
streamlit run app.py
```

Open the URL Streamlit prints (usually http://localhost:8501) and describe
yourself in the chat box, e.g.:

> I am a 22 year old woman from Himachal Pradesh. I belong to the SC category
> and want to start a dairy business.

The assistant will ask follow-up questions for any missing required details
(age, gender, state), then show a list of schemes with an eligibility badge,
a plain-language explanation, and step-by-step application instructions.

---

# Running Tests

```bash
pytest
```

Unit tests mock the LLM (`ollama`) calls and run fast. One test is marked
`integration` and queries the real, locally-built ChromaDB collection; it is
skipped automatically if `chroma_db/` hasn't been built yet.

```bash
pytest -m "not integration"   # unit tests only
pytest -m integration         # the ChromaDB integration test only
```

---

# Current Agents

- Profile Agent ✅
- Search Agent ✅
- Eligibility Agent ✅
- Explanation Agent ✅
- Action Agent ✅
- Orchestration Agent ✅

---

# Design Notes

- **Structured outputs.** Every LLM-backed agent asks Ollama for JSON
  constrained to a Pydantic model's schema (`utils/ollama_client.py`), then
  validates the response with that same model. This avoids brittle
  markdown/JSON-fence parsing and catches malformed model output as a typed
  `LLMResponseError` instead of a crash.
- **Deterministic where possible.** The Search Agent's retrieval and the
  Action Agent's apply-link extraction don't call the LLM at all — semantic
  search and regex are more reliable and cheaper than asking a small local
  model to reproduce facts that are already in the data.
- **State matching.** Scheme `state` values in the dataset are sometimes
  comma-separated lists (e.g. multi-state schemes) or `"All"`. Rather than a
  brittle exact-match ChromaDB metadata filter, the Search Agent does pure
  semantic retrieval and then re-ranks with a small boost for nationwide and
  matching-state schemes.
- **Graceful degradation.** If the local model returns something that
  doesn't validate, each agent falls back to a safe default (e.g.
  `insufficient_info` for eligibility) instead of failing the whole request.

---

# Team Workflow

After pulling the repository:

```bash
git pull
```

Install any newly added packages.

```bash
pip install -r requirements.txt
```

If the repository does **not** include the ChromaDB folder, generate it using:

```bash
python src/build_vectordb.py
```

---

# Development Workflow

1. Pull latest changes

```bash
git pull
```

2. Create a feature branch

```bash
git checkout -b feature/<feature-name>
```

3. Commit changes

```bash
git add .
git commit -m "Implemented <feature>"
```

4. Push

```bash
git push origin feature/<feature-name>
```

5. Create a Pull Request.

---

# Contributors

- Team Capstone Project
