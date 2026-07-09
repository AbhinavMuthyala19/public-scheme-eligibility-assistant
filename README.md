# Public Scheme Eligibility Assistant

An agentic AI application that helps Indian citizens discover government welfare
schemes they may qualify for. The user answers a few questions; the system
retrieves relevant schemes from ~4,700 schemes across India, checks eligibility
against each scheme's own rules using two LLMs in agreement, and returns a
plain-language, multilingual explanation with the documents needed and where to
apply.

The agents are orchestrated with **LangGraph**, and every eligibility decision
is cross-checked by **two LLMs (Claude + GPT)** so low-confidence answers can be
flagged for human review instead of guessed.

---

## Key ideas

- **RAG over all Indian schemes** — scheme text is chunked (with overlap) and
  embedded into ChromaDB; retrieval is filtered by the user's state so results
  are both relevant and geographically valid.
- **Grounded eligibility** — the Eligibility Agent judges the user only against
  each scheme's own eligibility text; it never invents criteria.
- **Multi-LLM confidence** — Claude and GPT both answer; agreement becomes a
  confidence score, and disagreement/uncertainty is flagged `needs review`.
- **Deterministic where it should be** — search filtering and the Action step
  (apply URLs) are plain code, not LLM calls.
- **Agentic orchestration** — a LangGraph `StateGraph` with conditional routing
  (a profile-completeness gate and a no-results gate).

---

## Architecture

```
                 ┌──────────────┐
   user form ──▶ │  Profile     │  build/validate profile
                 └──────┬───────┘
                        │  (missing State?) ──▶ clarify ▶ END
                        ▼
                 ┌──────────────┐
                 │  Search      │  RAG over ChromaDB + state filter
                 └──────┬───────┘
                        ▼
                 ┌──────────────┐
                 │  Eligibility │  Claude + GPT, grounded, confidence
                 └──────┬───────┘
                        │  (no matches?) ──▶ no_matches ▶ END
                        ▼
                 ┌──────────────┐
                 │  Explanation │  plain-language, multilingual
                 └──────┬───────┘
                        ▼
                 ┌──────────────┐
                 │  Action      │  apply URLs + next steps
                 └──────┬───────┘
                        ▼
                       END
```

The graph is defined in `graph.py`. Each node wraps one agent from `agents/`.

---

## Tech stack

- **Python**, **Streamlit** (UI)
- **LangGraph** (agent orchestration)
- **Anthropic Claude** + **OpenAI GPT** (multi-LLM ensemble)
- **ChromaDB** + **Sentence-Transformers** (`all-MiniLM-L6-v2`) for RAG
- **Pydantic** (typed state and schemas)

---

## Project structure

```
public-scheme-eligibility-assistant/
├── agents/
│   ├── profile_agent.py        # free-text -> structured profile (ensemble)
│   ├── search_agent.py         # profile -> query -> Chroma retrieval
│   ├── eligibility_agent.py    # grounded eligibility via Claude + GPT
│   ├── explanation_agent.py    # plain-language, multilingual summary
│   └── action_agent.py         # apply URLs + next steps (deterministic)
├── llm/
│   ├── providers.py            # Claude / GPT adapters behind one interface
│   └── ensemble.py             # call both, parse JSON, score agreement
├── prompts/                    # system prompts per agent
├── models/schemas.py           # Pydantic models (profile, verdicts, ...)
├── src/build_vectordb.py       # chunk + embed schemes into ChromaDB
├── retrieval.py                # Chroma search + chunk->scheme dedupe
├── scheme_store.py             # CSV lookup for full scheme text
├── graph.py                    # LangGraph StateGraph orchestration
├── app.py                      # Streamlit UI (runs through the graph)
├── eval/                       # golden test profiles + runner
├── data/merged_schemes.csv     # scheme dataset (~4,700 schemes)
├── config.py                   # paths, models, keys (from .env)
└── requirements.txt
```

---

## Setup

### 1. Virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. API keys

Copy `.env.example` to `.env` and add your keys (the file is gitignored):

```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

### 3. Build the vector database (one-time)

```bash
python3 src/build_vectordb.py
```

This chunks and embeds the schemes into `chroma_db/` (~19k chunks). It only
needs to be built once.

### 4. Run

```bash
streamlit run app.py
```

---

## How it works

1. **Profile** — the form (or free text via the Profile Agent) produces a typed
   `UserProfile`. If State is missing, the graph routes to a clarify step.
2. **Search** — the profile becomes a semantic query; ChromaDB returns the most
   relevant schemes, filtered to the user's state plus nationally-available
   ("All") schemes.
3. **Eligibility** — for each candidate, Claude and GPT independently judge the
   profile against the scheme's eligibility text and extract required documents.
   Their agreement is the confidence; disagreement or "unclear" is flagged.
4. **Explanation** — a single model writes a friendly, grounded summary in the
   chosen language.
5. **Action** — apply URLs and next steps are pulled straight from the data.

---

## Evaluation

```bash
python3 eval/run_eval.py
```

Runs a set of golden test profiles through the pipeline and checks structural
correctness (results returned, state filter respected, no ineligible schemes
shown).

---

## Notes

- Eligibility is LLM-assisted because the scheme rules are free text, not
  structured fields; it is grounded and confidence-flagged to stay responsible.
- This tool provides guidance only — users should confirm on the official
  government portal before applying.
