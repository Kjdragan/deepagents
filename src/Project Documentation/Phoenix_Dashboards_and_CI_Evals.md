# Phoenix Dashboards and CI Evals Integration Guide

This document explains the monitoring and evaluation features added to DeepAgents:
- Phoenix/Arize dashboards with curated saved views and shareable links
- Automated evaluation runs in CI and optional local post-run evals

Use this guide to configure, run, and inspect results.

---

## What’s included

- Tracing attributes for dashboard filtering:
  - `graph.node.id`, `graph.node.parent_id`, `agent.type`
  - `run.id`, `session.id`
  - `llm.input_tokens`, `llm.output_tokens`, `llm.total_tokens`, `llm.cost_usd`
  - `error.type`, `error.message`
- Local run/session IDs are generated and exported per run to ensure consistent filtering.
- Optional local post-run evals.
- GitHub Actions workflow that compiles run snapshots and executes Phoenix LLM-as-a-Judge, publishing CSV artifacts.

Key files:
- `examples/research/dump_run.py` — creates `run.id`/`session.id`, writes outputs, optional auto-evals
- `examples/research/eval_run.py` — compiles runs and executes evals, writes CSVs
- `src/deepagents/graph.py` — root agent metadata enriched with run/session
- `src/deepagents/sub_agent.py` — sub-agent metadata enriched with run/session
- `src/deepagents/tracing.py` — OTEL callback attaches attributes to LLM and error spans
- `docs/phoenix_dashboards.md` — dashboard recipes, curated views, sharing links
- `.github/workflows/research-evals.yml` — CI job to compile + eval + upload artifacts

---

## Prerequisites

- Install dependencies (repo already pins core libs):
  - `openinference-instrumentation-langchain`, `arize-otel`, `opentelemetry-sdk`
  - For evals: `pandas`, `arize-phoenix`
- Environment variables:
  - Arize/Phoenix tracing: `ARIZE_API_KEY`, `ARIZE_SPACE_ID`
  - Optional pricing (for cost attribution): `LLM_PRICE_INPUT_PER_1K`, `LLM_PRICE_OUTPUT_PER_1K`
  - CI evals: `OPENAI_API_KEY` (as a GitHub repo secret)

---

## Running locally with tracing and optional post-run evals

1) Optional: group multiple runs into a session
```bash
export DEEPAGENTS_SESSION_ID=my-session-001
```

2) Optional: enable auto-evals after each dump and choose evaluator model
```bash
export DEEPAGENTS_RUN_EVALS=1
export DEEPAGENTS_EVAL_MODEL=gpt-4o-mini
```

3) Execute a research run
```bash
uv run python examples/research/dump_run.py "Your research question"
```

Outputs in `outputs/` include:
- `run_state_<timestamp>.json` — snapshot
- `<timestamp>__events.jsonl` — events log
- `<timestamp>__report.md` — final summary/report
- When auto-evals enabled:
  - `compiled_runs.csv` — compiled run data
  - `eval_results.csv` — evaluation results

Note: `dump_run.py` loads `eval_run.py` via file path (importlib), so local auto-evals work without altering PYTHONPATH.

---

## Phoenix/Arize dashboards

- Attribute coverage and suggested widgets/filters are documented in `docs/phoenix_dashboards.md`.
- Common filters you can save/share:
  - `agent.type = main-agent` (last 24h)
  - `graph.node.parent_id != null` (sub-agents)
  - `llm.cost_usd > 0.50` (high-cost runs)
  - `llm.total_tokens > 20000` (token-heavy runs)
  - `error.type != null` (errored traces)
  - `run.id = <from output filename>`
  - `session.id = <your session>`

Sharing links:
- Apply filters and time range → Save View in Arize → copy the browser URL. The link preserves filters and the saved view.

Where to access:
- Arize Phoenix: `https://app.arize.com/spaces/$ARIZE_SPACE_ID/phoenix`

---

## CI: Automated evals on push

Workflow: `.github/workflows/research-evals.yml`
- Trigger: push with paths:
  - `outputs/run_state_*.json`
  - `.github/workflows/research-evals.yml`
- Steps:
  1. Checkout, setup Python 3.11
  2. `pip install . && pip install pandas arize-phoenix`
  3. Compile runs: `python examples/research/eval_run.py --outputs-dir outputs`
  4. Run evals: `python examples/research/eval_run.py --outputs-dir outputs --run-evals --evaluator-model "$EVALUATOR_MODEL"`
  5. Upload artifacts: `outputs/compiled_runs.csv`, `outputs/eval_results.csv`

Secrets required:
- `OPENAI_API_KEY` — set in repo settings → Secrets and variables → Actions

Accessing results:
- Navigate to the workflow run → Artifacts → `research-evals-<run_id>`
- Download CSVs for analysis & sharing

Notes:
- If you prefer not to commit `outputs/` snapshots, add an alternate trigger (e.g., `workflow_dispatch`, schedule) and fetch artifacts from your storage.

---

## Troubleshooting

- No spans in Phoenix:
  - Verify `ARIZE_API_KEY`/`ARIZE_SPACE_ID` env vars
  - Ensure tracing is initialized in `src/deepagents/tracing.py` by your entrypoint
- Missing cost in spans:
  - Check pricing env vars are set; ensure models report token usage
- CI evals don’t run:
  - Confirm that a `run_state_*.json` was committed and pushed
  - Ensure `OPENAI_API_KEY` secret exists
- Local auto-evals don’t run:
  - Verify `DEEPAGENTS_RUN_EVALS=1`; check console for suppressed exceptions

---

## Related docs

- `docs/phoenix_dashboards.md` — detailed dashboard setup, widgets, saved views, and link sharing
- `docs/how to run this.md` — general project run instructions
- `src/Project Documentation/research_flow.md` — architecture and research agent flow

---

## Change summary (what was added)

- Run/session tagging propagated across root and sub-agents; spans enriched with tokens, cost, and error fields
- Optional local post-run evals invoked from `dump_run.py`
- CI workflow compiles and evaluates runs, uploading CSV artifacts
- Documentation for dashboards, saved views, and usage
