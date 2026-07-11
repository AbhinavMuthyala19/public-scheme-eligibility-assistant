# Deployment (Railway + Chroma Cloud)

The app is stateless: embeddings come from the OpenAI API and vectors live in
Chroma Cloud, so nothing heavy ships in the container.

## 1. Create a Chroma Cloud database

1. Sign up at https://www.trychroma.com (free serverless tier).
2. Create a database and copy the **API key**, **tenant**, and **database name**.

## 2. Build the vector DB into Chroma Cloud (one-time, from your machine)

Put the Chroma Cloud values in your local `.env` (alongside the API keys):

```
CHROMA_API_KEY=ck-...
CHROMA_TENANT=...
CHROMA_DATABASE=...
```

Then build (this embeds ~19k chunks via OpenAI and uploads them):

```bash
python3 src/build_vectordb.py
```

It should end with `Chunks in DB: 19438`. You only do this once (rerun if the
scheme data changes).

## 3. Deploy on Railway

1. Push your branch to GitHub.
2. Railway → **New Project → Deploy from GitHub repo** → pick this repo/branch.
3. Under **Variables**, add:
   - `ANTHROPIC_API_KEY`
   - `OPENAI_API_KEY`
   - `CHROMA_API_KEY`
   - `CHROMA_TENANT`
   - `CHROMA_DATABASE`
4. Railway auto-detects Python + `requirements.txt` and uses the `Procfile`
   start command. Deploy.

No volume, no torch, no DB build on the server — the app just queries Chroma
Cloud. Cold starts are fast.

## Local development

Leave the `CHROMA_*` variables set to use the same cloud DB locally, or unset
them to fall back to a local `./chroma_db` (which you'd build the same way).
