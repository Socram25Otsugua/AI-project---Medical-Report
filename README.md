# Offline AI Radio Medical Report Reviewer

Offline application to **evaluate clinical reports (Radio Medical Record)**, identify omissions/gaps, and generate **situational responses** (next treatment step) as an alternative/supplement to prebuilt responses.

## Architecture (project requirements)

- **Frontend**: React (Vite + TypeScript)
- **Backend**: Python **FastAPI** (REST)
- **LLM**: **Ollama** (standard model; optional custom Modelfile)
- **Orchestration**: **LangChain** (prompts, chains, tools, memory)
- **RAG**: local knowledge base (vector store)
- **MCP**: local tools/context server (offline) consumed by LangChain
- **Prompt testing**: Promptfoo
- **Tests**: unit tests for core components (backend and frontend)

## How to run locally

### 1) Prerequisites

- Python 3.11+
- Node 18+
- [Ollama](https://ollama.com/) installed and running

### 2) Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3) Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the UI and submit a report to get **structured feedback** + a **recommended response**.

## Ollama Models

By default, the backend uses `llama3.1` (configurable via `OLLAMA_MODEL`). If you want a custom model, place the `Modelfile` in `ollama/Modelfile` and document it in the model README.

## Prompt Tests (Promptfoo)

Prompt tests live in `promptfoo/` and use the `ollama:chat` provider.

```bash
cd promptfoo
# In restricted-network environments, skip Playwright download:
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm install
export OLLAMA_BASE_URL="http://127.0.0.1:11434"
npm run test:prompts
```

## Unit Tests

### Frontend

```bash
cd frontend
npm install
npm test -- --run
```

### Backend

```bash
cd backend
pip install -r requirements.txt
pytest
```