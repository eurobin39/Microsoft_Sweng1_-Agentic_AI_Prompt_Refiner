# Agentic AI Prompt Refiner

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/extract-blueprints` | Crawl repo → return one `AgentBlueprintWithTraces` per agent |
| `POST` | `/api/v1/refine-all` | Run judge + refiner on a list of agent blueprints |
| `POST` | `/api/v1/extract-blueprint` | Single-agent blueprint extraction (legacy) |
| `POST` | `/api/v1/evaluate` | Evaluate one blueprint + traces |
| `GET`  | `/api/health` | Health check |

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
AZURE_OPENAI_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
GITHUB_TOKEN=ghp_...   # optional — increases GitHub API rate limit
```

Start the server:

```bash
uvicorn app.main:app --reload
# runs on http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# runs on http://localhost:3000
```

## Demo Agents

Three example repos are included under `backend/app/demos/` to test the full pipeline:

| Demo | Agents | Pattern |
|------|--------|---------|
| `code_assistant` | triage · explainer · refactor · documenter | Handoff |
| `resume_assistant` | router · collector · analyzer · writer · reviewer | DAG with conditional routing |
| `travel_assistant` | triage · weather · packing · activities · booking | Handoff with chaining |

Each demo has a `ground_truth.json` with expected agent behavior and tool calls, and a `log/traces/` directory with real execution traces.

To run a demo locally:

```bash
cd backend
source venv/bin/activate
python app/demos/code_assistant/demo.py
```