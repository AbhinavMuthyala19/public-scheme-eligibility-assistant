````markdown
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

---

# Project Architecture

```
User
    │
    ▼
Orchestration Agent
    │
    ▼
Profile Agent
    │
    ▼
Search Agent
    │
    ▼
Eligibility Agent
    │
    ▼
Explanation Agent
    │
    ▼
Action Agent
```

---

# Folder Structure

```
SchemesProject/
│
├── agents/
│
├── chroma_db/
│
├── data/
│   └── merged_schemes.csv
│
├── models/
│
├── prompts/
│
├── utils/
│
├── app.py
├── config.py
├── requirements.txt
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

The vector database only needs to be built once.

---

# Running the Application

Run Streamlit.

```bash
streamlit run app.py
```

---

# Current Agents

- Profile Agent ✅
- Search Agent
- Eligibility Agent
- Explanation Agent
- Action Agent
- Orchestration Agent

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
````
