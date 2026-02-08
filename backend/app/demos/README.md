# Demos

This folder contains three multi-agent demo applications, each showcasing an orchestrator pattern that routes user requests to specialized AI agents powered by Azure OpenAI.

## Project Structure

```
demos/
├── code_assistant/
│   ├── __init__.py
│   ├── orchestrator.py
│   ├── code_explainer_agent.py
│   ├── code_refactor_agent.py
│   ├── code_documentation_agent.py
│   └── demo.py
├── resume_builder/
│   ├── __init__.py
│   ├── orchestrator.py
│   ├── info_collector_agent.py
│   ├── job_analysis_agent.py
│   ├── resume_writer_agent.py
│   ├── resume_feedback_agent.py
│   └── demo.py
├── travel_assistant/
│   ├── __init__.py
│   ├── orchestrator.py
│   ├── travel_weather_agent.py
│   ├── travel_packing_agent.py
│   └── demo.py
└── README.md
```

## Architecture

All three demos follow the same pattern:

1. **User request** comes into the orchestrator
2. The **orchestrator** uses an LLM call to classify the user's intent
3. Based on the intent, the orchestrator **routes** to one or more specialized agents
4. Each **agent** makes its own LLM call with a focused system prompt
5. Results are returned (and optionally **streamed** to the console)

```
User Request
     │
     ▼
┌─────────-───┐    classify     ┌──────────┐
│ Orchestrator│ ──────────────▶ │  Agent A │
│  (router)   │                 ├──────────┤
│             │ ──────────────▶ │  Agent B │
│             │                 ├──────────┤
│             │ ──────────────▶ │  Agent C │
└─────────-───┘                 └──────────┘
     │
     ▼
  Combined Response
```

---

## 1. Code Assistant

A multi-agent system for code analysis, refactoring, and documentation.

### Agents

| Agent | File | Description |
|-------|------|-------------|
| **Code Explainer** | `code_explainer_agent.py` | Explains what code does in plain English with step-by-step breakdowns |
| **Code Refactor** | `code_refactor_agent.py` | Improves code quality, structure, and performance. Accepts an optional `refactor_goal` parameter |
| **Code Documentation** | `code_documentation_agent.py` | Adds docstrings and inline comments. Supports Google, NumPy, Sphinx, and PEP 257 styles |

### Orchestrator Intents

- `explain` — Route to the explainer agent
- `refactor` — Route to the refactor agent (extracts goal if specified)
- `document` — Route to the documentation agent (extracts doc style if specified)
- `multiple` — Chain agents sequentially (e.g., refactor then document, with the refactored code passed to the next step)

---

## 2. Resume Builder

A multi-agent pipeline that builds tailored resumes from natural language input and job descriptions.

### Agents

| Agent | File | Description |
|-------|------|-------------|
| **Info Collector** | `info_collector_agent.py` | Extracts structured profile data (name, education, skills, experience, etc.) from natural language input |
| **Job Analyzer** | `job_analysis_agent.py` | Parses a job description into required skills, preferred skills, ATS keywords, experience level, and domain |
| **Resume Writer** | `resume_writer_agent.py` | Generates a professional, tailored resume in Markdown using profile data and job analysis |
| **Resume Reviewer** | `resume_feedback_agent.py` | Scores the resume, identifies strengths, keyword gaps, and provides concrete rewrite suggestions |

### Orchestrator Intents

- `full_pipeline` — Runs all 4 agents in sequence: collect → analyze → write → review
- `write_only` — Skips info collection; writes a resume directly from provided data
- `review_only` — Reviews an existing resume against a job description
- `analyze_job` — Only analyzes the job posting

---

## 3. Travel Assistant

A multi-agent system that provides weather information and packing suggestions for travel destinations.

### Agents

| Agent | File | Description |
|-------|------|-------------|
| **Weather Agent** | `travel_weather_agent.py` | Retrieves weather information for a given destination |
| **Packing Agent** | `travel_packing_agent.py` | Generates packing suggestions based on weather conditions |

### Orchestrator Intents

- `weather` — Route to the weather agent only
- `packing` — Fetch weather first, then generate packing suggestions based on conditions
- `both` — Run both agents and compose a friendly combined response using an additional LLM call

---

### Install Dependencies

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

---

## Running the Demos

Make sure you're in the `backend/` directory with your venv activated.

```bash
# Code Assistant
python -m app.demos.code_assistant.demo

# Resume Builder
python -m app.demos.resume_builder.demo

# Travel Assistant
python -m app.demos.travel_assistant.demo
```

All demos use `stream=True` by default, so you'll see responses printed to the console in real time.