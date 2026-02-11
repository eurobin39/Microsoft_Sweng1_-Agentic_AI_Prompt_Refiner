# Travel Assistant — Microsoft Agent Framework

Multi-agent travel assistant demonstrating three orchestration patterns from the [Microsoft Agent Framework](https://github.com/microsoft/agent-framework).

## Architecture

### Handoff Workflow (primary)
```
User → TriageAgent ─┬── handoff → WeatherAgent ──┬── handoff → PackingAgent
                     ├── handoff → PackingAgent    └── handoff → ActivitiesAgent
                     ├── handoff → ActivitiesAgent ── handoff → BookingAgent
                     └── handoff → BookingAgent    ── handoff → WeatherAgent
```
Triage classifies intent and routes to specialists. Specialists can hand off to each other for multi-topic requests. Full conversation history is preserved across all transitions.

### Sequential Workflow
```
User → WeatherAgent → PackingAgent → Output
```
Packing agent sees weather context in conversation history, so suggestions are weather-appropriate.

### Concurrent Workflow
```
User ──┬── WeatherAgent   ──┐
       ├── ActivitiesAgent ──┼── Custom Aggregator → Combined Output
       └── BookingAgent    ──┘
```
All three agents process the same request in parallel. Results are merged by a custom aggregator.

## Agents & Tools

| Agent | Tools | Hands off to |
|-------|-------|-------------|
| **TriageAgent** | *(handoff tools auto-registered)* | All specialists |
| **WeatherAgent** | `get_weather`, `get_forecast` | Packing, Activities |
| **PackingAgent** | `get_packing_list`, `check_luggage_restrictions` | — |
| **ActivitiesAgent** | `get_activities`, `get_local_tips` | Booking |
| **BookingAgent** | `search_flights`, `search_hotels`, `book_flight`, `book_hotel` | Weather |

## Setup

```bash
python -m travel_assistant.demo
```

## Logging

Every workflow event is logged with timestamps and executor IDs:
- `▶ INVOKED` — executor started
- `✓ COMPLETE` — executor finished (with duration in ms)
- `⚡ STREAM` — agent streaming tokens (DEBUG level)
- `📦 OUTPUT` — intermediate outputs
- `🏁 FINAL` — workflow result

Logs go to console + optional file. Review for prompt refinement and debugging.

## Project Structure

```
travel_assistant/
├── __init__.py
├── runner.py              # Unified entry point for all workflows
├── mock_data.py           # Rich mock data (swap to real APIs later)
├── logger.py              # Workflow event logging
├── demo.py                # Demo with 5 test scenarios
├── .env.example
├── requirements.txt
├── agents/
│   └── definitions.py     # All 5 agents + 12 tools
└── workflows/
    ├── handoff.py          # HandoffBuilder — triage routing
    ├── concurrent.py       # ConcurrentBuilder — parallel agents
    └── sequential.py       # SequentialBuilder — chained pipeline
```

## Key Framework Features Used

| Feature | From | Used for |
|---------|------|----------|
| `HandoffBuilder` | `agent_framework.orchestrations` | Triage → specialist routing with directed handoffs |
| `ConcurrentBuilder` | `agent_framework.orchestrations` | Parallel fan-out with custom aggregator |
| `SequentialBuilder` | `agent_framework.orchestrations` | Chained agent pipeline |
| `ChatAgent` | `agent_framework` | Agent creation with tools |
| `@ai_function` | `agent_framework` | Tool registration with auto schema |
| `AzureOpenAIChatClient` | `agent_framework.azure` | Azure OpenAI integration |
| Event streaming | `workflow.run(stream=True)` | Real-time observability |

## Swapping to Real APIs

Each tool in `mock_data.py` has a clean signature. Replace the function body:

```python
# Before:
def mock_search_flights(origin, destination, date):
    return json.dumps({...fake...})

# After:
def mock_search_flights(origin, destination, date):
    return json.dumps(amadeus_client.search(origin, destination, date).data)
```

Agents, workflows, and logging are unchanged.