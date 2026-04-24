# Offline AI Radio Medical Report Reviewer

Aplicação offline para **avaliar relatórios clínicos (Radio Medical Record)**, identificar omissões/deficiências e gerar **respostas situacionais** (próximo passo de tratamento) como alternativa/suplemento a respostas pré-fabricadas.

## Arquitetura (requisitos do projeto)

- **Frontend**: React (Vite + TypeScript)
- **Backend**: Python **FastAPI** (REST)
- **LLM**: **Ollama** (modelo standard; opcional: custom Modelfile)
- **Orquestração**: **LangChain** (prompts, chains, tools, memória)
- **RAG**: base de conhecimento local (vector store)
- **MCP**: servidor local de ferramentas/contexto (offline) consumido pelo LangChain
- **Prompt testing**: Promptfoo
- **Testes**: unit tests para componentes core (backend e frontend)

## Como correr localmente

### 1) Pré‑requisitos

- Python 3.11+
- Node 18+
- [Ollama](https://ollama.com/) instalado e a correr

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

Abra a UI e submeta um relatório para obter **feedback estruturado** + **resposta recomendada**.

## Modelos Ollama

Por defeito, o backend usa `llama3.1` (configurável por `OLLAMA_MODEL`). Se quiseres um modelo custom, coloca o `Modelfile` em `ollama/Modelfile` e documenta no README do modelo.

## Prompt tests (Promptfoo)

Os testes de prompts vivem em `promptfoo/` e usam o provider `ollama:chat`.

```bash
cd promptfoo
# Em ambientes com rede restrita, evita download do Playwright:
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm install
export OLLAMA_BASE_URL="http://127.0.0.1:11434"
npm run test:prompts
```

## Testes unitários

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