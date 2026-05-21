# Prompt evaluation suite

Contract tests for the Radio Medical AI **review** and **response** system prompts. Evaluations call Ollama locally and assert JSON shape and clinically reasonable behaviour — not exact wording — so results stay stable across non-deterministic model output.

## Layout

| Path | Purpose |
|------|---------|
| `prompts/review.txt` | Review chain system prompt (mirrors `backend/app/prompts/review_form_prompt.py`) |
| `prompts/response.txt` | Response chain system prompt (mirrors `backend/app/prompts/response_prompt.py`) |
| `fixtures/` | Synthetic training reports and stub review JSON for response tests |
| `assertions/` | Reusable JavaScript assertions loaded via `file://` |
| `lib/parse-output.cjs` | Shared JSON extraction from model output |
| `promptfooconfig.review.yaml` | Review-only eval config |
| `promptfooconfig.response.yaml` | Response-only eval config |
| `promptfooconfig.yaml` | Combined suite (optional) |

## Prerequisites

- [Ollama](https://ollama.com/) running with `llama3.1` (configured in the YAML configs)
- Node.js 20+

## Run locally

```bash
cd promptfoo
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm install
export OLLAMA_BASE_URL="http://127.0.0.1:11434"
npm run test:prompts
```

Individual suites:

```bash
npm run test:prompts:review
npm run test:prompts:response
npm run view    # open last eval in the Promptfoo UI
```

## What is tested

### Review (`promptfooconfig.review.yaml`)

| Case | Fixture | Expectation |
|------|---------|-------------|
| Complete ABCDE report | `fixtures/report_minimal.txt` | Valid JSON with `completeness_score`, `deficiencies[]`, `safety_flags[]` |
| Undocumented vitals | `fixtures/report_missing_vitals.txt` | Valid JSON with `completeness_score` ≤ 70 |

### Response (`promptfooconfig.response.yaml`)

| Case | Fixtures | Expectation |
|------|----------|-------------|
| Action plan for complete report | `report_minimal.txt` + `review_complete.json` | Non-empty `immediate_actions[]` plus monitoring, escalation, rationale, and questions arrays |
| Vitals gap for sparse report | `report_missing_vitals.txt` + `review_sparse.json` | Follow-up questions or `immediate_actions` that explicitly address obtaining/documenting vitals |

## Scope and limitations

These evals validate **prompt contracts** against Ollama without the full FastAPI stack. They do not exercise RAG retrieval, session memory, or MCP enrichment. When changing production prompts in `backend/app/prompts/`, update the matching files under `prompts/` so CI stays aligned.

## CI

Pull requests run this suite in `.github/workflows/pr-checks.yml` after installing Ollama and pulling `llama3.1`.
