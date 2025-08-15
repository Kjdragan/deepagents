# Phoenix/Arize Dashboards Spec for DeepAgents

This spec defines the initial set of dashboards and widgets in Arize to monitor DeepAgents research runs. It complements the tracing already initialized in `src/deepagents/tracing.py` and the agent orchestration in `src/deepagents/graph.py` and `src/deepagents/sub_agent.py`.

Links:
- Arize Dashboards: https://arize.com/docs/ax/observe/dashboards
- Implementing Agent Metadata: https://arize.com/docs/ax/observe/agents/implementing-agent-metadata-for-arize
- Setup tracing: https://arize.com/docs/ax/observe/tracing/set-up-tracing

## Goals
- Monitor health and efficiency of research runs over time.
- Drill down by agent, sub-agent, and tool.
- Quickly surface errors, slow paths, and high token/cost outliers.

## Prereqs
- Env vars: `ARIZE_API_KEY`, `ARIZE_SPACE_ID` (see `src/deepagents/tracing.py`).
- Py deps (already present): `openinference-instrumentation-langchain`, `arize-otel`, `opentelemetry-sdk`.
- Optional quick link: `get_arize_dashboard_url(project_name)` in `src/deepagents/tracing.py`.

## Span attributes to emit (for better filtering/aggregation)
These attributes are attached to agent and LLM/tool spans via `with_config(metadata=...)` and the OTEL callback in `src/deepagents/tracing.py`.

- `graph.node.id` (string) — e.g., `agent-<id>`, `subagent-<type>-<id>`.
- `graph.node.parent_id` (string) — set for sub-agents.
- `agent.type` (string) — `main-agent`, specific sub-agent name, etc.
- `run.id` (string) — per invocation (set by `examples/research/dump_run.py`).
- `session.id` (string) — groups multiple runs in a session.
- `llm.input_tokens`, `llm.output_tokens`, `llm.total_tokens` — populated from model usage when available.
- `llm.cost_usd` — computed from `.env` pricing variables if provided.
- `error.type`, `error.message` — set on error spans.

Already implemented in code: `graph.node.id`, `graph.node.parent_id`, `agent.type`, `run.id`, `session.id`, token counters, and `llm.cost_usd`.

## Dashboard 1: Run Overview
- Filters (default):
  - project: `deepagents`
  - time range: last 24h (editable)
- Widgets:
  - Timeseries: Requests count by `agent.type`.
  - Timeseries: Latency P50/P95 by `agent.type`.
  - Timeseries: Tokens total by `agent.type`.
  - Timeseries: Cost (USD) by `agent.type` (if available).
  - Table: Top runs by `latency.ms` (show `run.id`, `agent.type`, `model.name`).
  - Table: Top errors (count by `error.type`, include example links).

## Dashboard 2: React Loop Health
- Focus: LangGraph loop iterations, tool thinking vs acting.
- Widgets:
  - Timeseries: Tool-call count per run (sum), grouped by `agent.type`.
  - Distribution: `latency.ms` histogram for tool spans.
  - Table: Slowest tool calls (mean `latency.ms`), grouped by `tool.name`.
  - Timeseries: Tokens per step (approx by tool LLM spans), grouped by `tool.name`.
  - Text: Link to sequence diagrams in `docs/research_flow.md` for reference.

## Dashboard 3: Tool Performance
- Widgets:
  - Timeseries: Error rate by `tool.name` (`error.type` != null / calls).
  - Timeseries: Latency P95 by `tool.name`.
  - Table: Top N tool failures with sample trace links.
  - Distribution: Tokens per tool call.

## Dashboard 4: Sub-Agent Tree & Handoffs
- Widgets:
  - Timeseries: Sub-agent invocations by `agent.type`.
  - Table: Parent→Child handoffs (counts grouped by `graph.node.parent_id`→`graph.node.id`).
  - Distribution: Latency per sub-agent type.
  - Built-in trace view: Use the multi-agent visualization to inspect hierarchies.

## Dashboard 5: Cost & Efficiency
- Widgets:
  - Timeseries: Cost (USD) by `agent.type` and `model.name`.
  - Timeseries: Tokens per request (prompt vs completion stacked).
  - Table: Most expensive runs (top `run.id` by cost, with filters to drill down).

## Curated Saved Views (Filters you can save and share)
- `agent.type = main-agent` (time range: last 24h)
- `agent.type = research-agent` (time range: last 7d)
- `graph.node.parent_id != null` (sub-agent spans only)
- `llm.cost_usd > 0.50` (high-cost runs)
- `llm.total_tokens > 20000` (token-heavy runs)
- `error.type != null` (errored traces)
- `run.id = <paste from outputs filename>` (deep dive a single run)
- `session.id = <your session>` (group of related runs)

## Saved Views (Filters)
- `agent.type = main-agent`
- `agent.type = research-agent`
- `tool.name = write_file | edit_file | read_file | ls`
- `error.type != null`
- `model.name = claude-3-5-sonnet-latest` (example)

## How to create in Arize
1. Open Dashboards → New Dashboard → Set name (e.g., "DeepAgents — Run Overview").
2. Add timeseries/distribution/table widgets per above using attributes as dimensions.
3. Save default filters; create Saved Views for common filters.
4. Share dashboard link with team. Optionally wire monitors/alerts in Arize.

### Sharing direct links
- Apply your filters and time range, then use "Save view" (or equivalent) in the dashboard UI.
- Copy the browser URL; Arize preserves filters and the saved view in the link.
- Tip: include `run.id` or `session.id` filters before copying to share a stable investigation link.

### Saved View URLs (paste-ready for your team)
Paste the saved-view URLs you create in Arize below, so the team can access them quickly:

- Main Agent (last 24h): <PASTE_URL_HERE>
- Research Agent (last 7d): <PASTE_URL_HERE>
- Sub-agent spans only (`graph.node.parent_id != null`): <PASTE_URL_HERE>
- High-cost runs (`llm.cost_usd > 0.50`): <PASTE_URL_HERE>
- High-token runs (`llm.total_tokens > 20000`): <PASTE_URL_HERE>
- Errors only (`error.type != null`): <PASTE_URL_HERE>
- Single run (filter by `run.id = …`): <PASTE_URL_HERE>
- Session view (filter by `session.id = …`): <PASTE_URL_HERE>

## Next Steps
- Implement additional span attributes in code (TODO t7).
- Add cost calculator if desired.
- Iterate widgets based on observed traces and team feedback.
