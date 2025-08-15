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
Today we emit `graph.node.id` (+ optional `graph.node.parent_id`). For richer dashboards, add these attributes to spans (model, tool, and agent spans). These can be attached via LangChain run metadata and picked up by OpenInference.

- `graph.node.id` (string) — required. e.g., `agent-1234`, `subagent-research-5678`.
- `graph.node.parent_id` (string) — optional for sub-agents.
- `agent.type` (string) — `main-agent`, `research-agent`, `critique-agent`, etc.
- `tool.name` (string) — for tool spans.
- `run.id` (string) — stable per invocation; use UUID.
- `session.id` (string) — group related runs, e.g., CLI session.
- `model.name` (string), `model.provider` (string), `model.temperature` (number).
- `latency.ms` (number) — auto-captured for LLM/tool spans.
- `tokens.prompt` (number), `tokens.completion` (number), `tokens.total` (number). If available.
- `cost.usd` (number) — if a cost calculator is added.
- `error.type` (string), `error.message` (string) — when exceptions occur.
- `prompt.version` (string) — if you version prompts in `src/deepagents/prompts.py`.

Note: Implementing the bolded items can be done incrementally in `graph.py`/`sub_agent.py` by passing `metadata` on LC calls and/or using callbacks. See "Implementing Agent Metadata" docs above. (Tracked in TODO t7.)

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

## Next Steps
- Implement additional span attributes in code (TODO t7).
- Add cost calculator if desired.
- Iterate widgets based on observed traces and team feedback.
