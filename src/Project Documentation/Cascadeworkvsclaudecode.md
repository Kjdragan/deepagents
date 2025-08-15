# Cascade Work vs. Claude Code – DeepAgents Tracing + Dev-Mode Enhancements

This report documents the work completed to enhance DeepAgents with richer Phoenix/Arize tracing (token usage, cost estimation, and error attributes), add development-mode limiting controls, and ensure final report outputs are generated reliably for research runs. It also records how cost pricing is configured for the current model.

## What Was Implemented

- **Tracing enrichment (tokens, cost, errors)**
  - Implemented `_OTelSpanEnricher` LangChain callback in `src/deepagents/tracing.py` to add span attributes:
    - `llm.input_tokens`, `llm.output_tokens`, `llm.total_tokens`
    - Optional `llm.cost_usd` if pricing env vars are present
    - Error metadata on LLM/chain/tool errors
  - Attached the callback to the main agent and sub-agents so all spans are enriched:
    - Main agent: `src/deepagents/graph.py` in `create_deep_agent()` via `with_config(callbacks=[get_tracing_callback_handler()])`
    - Sub-agents: `src/deepagents/sub_agent.py` inside `task` tool before invocation

- **Development mode limiting (runtime/token control)**
  - Added environment-controlled limits in `examples/research/research_agent.py`:
    - `DEEPAGENTS_DEV_MODE` (boolean)
    - `DEEPAGENTS_MAX_STEPS` (LangGraph recursion_limit)
    - `DEEPAGENTS_MAX_SEARCH_RESULTS` (per Tavily search)
  - Limits are attached to agent metadata for trace visibility (`dev_mode`, `limits.max_steps`, `limits.max_search_results`).
  - Search tool enforces hard cap regardless of passed parameters.

- **Dump runner resilience**
  - `examples/research/dump_run.py` hardened to handle `GraphRecursionError` and asyncio loop edge-cases gracefully, persist error event lines to `__events.jsonl`, and still attempt to write a final state/report.

- **Documentation updates**
  - `src/Project Documentation/how to run this.md` updated with:
    - Dev-mode variables and usage
    - Cost pricing env vars and how they’re consumed by tracing

## Where Pricing Gets Set

- Pricing for cost estimation is read by `_OTelSpanEnricher._maybe_cost()` in `src/deepagents/tracing.py`.
- It looks for these environment variables (USD per 1K tokens):
  - `LLM_PRICE_INPUT_PER_1K`
  - `LLM_PRICE_OUTPUT_PER_1K`
- When these are set, the callback computes `llm.cost_usd` as:
  - `input_tokens/1000 * LLM_PRICE_INPUT_PER_1K + output_tokens/1000 * LLM_PRICE_OUTPUT_PER_1K`

### Current Pricing (set in `.env`)

```
LLM_PRICE_INPUT_PER_1K=3.00
LLM_PRICE_OUTPUT_PER_1K=15.00
```

These correspond to the requested pricing for the Sonnet 4 model.

## Files Updated

- `src/deepagents/graph.py`
  - Attach Arize metadata and tracing callback to the main agent for enriched spans.
- `src/deepagents/sub_agent.py`
  - Attach Arize metadata and tracing callback to sub-agents created inside the `task` tool.
- `examples/research/dump_run.py`
  - Add robust error handling for streaming and event loop usage; write error events to `__events.jsonl`.
- `src/Project Documentation/how to run this.md`
  - Add a section on development mode limits and cost environment variables.
- `.env`
  - Add pricing variables: `LLM_PRICE_INPUT_PER_1K=3.00`, `LLM_PRICE_OUTPUT_PER_1K=15.00`.

## How to Use

- Ensure tracing env vars are set (`ARIZE_API_KEY`, `ARIZE_SPACE_ID`) and add pricing if you want cost estimation.
- Enable development mode for faster/cheaper runs:

```bash
DEEPAGENTS_DEV_MODE=1 DEEPAGENTS_MAX_STEPS=60 DEEPAGENTS_MAX_SEARCH_RESULTS=2 \
  uv run --env-file .env python examples/research/dump_run.py "Your research question"
```

- Compile results and (optionally) run evals:

```bash
uv run --env-file .env python examples/research/eval_run.py
uv run --env-file .env python examples/research/eval_run.py --run-evals --evaluator-model gpt-4o-mini
```

## Outputs Verified

Recent dev-mode run produced (examples):
- `outputs/20250814_214021__events.jsonl`
- `outputs/20250814_214021__final_report.md`
- `outputs/20250814_214021__question.txt`
- `outputs/run_state_20250814_214021.json|.txt`
- `outputs/compiled_runs.csv` updated with rows for the latest runs

## Tracing Verification

- Check Arize/Phoenix dashboard for spans from the recent run.
- You should see attributes on LLM spans:
  - `llm.input_tokens`, `llm.output_tokens`, `llm.total_tokens`
  - `llm.cost_usd` if pricing env vars are set (.env pricing included above)
  - Error attributes present on exceptions

## Related Docs and Entrypoints

- Tracing: `src/deepagents/tracing.py`
- Main agent construction: `src/deepagents/graph.py`
- Sub-agents: `src/deepagents/sub_agent.py`
- Example research agent: `examples/research/research_agent.py`
- Dump runner: `examples/research/dump_run.py`
- CLI help and model selection: `src/deepagents/cli.py`
- Research flow docs: `src/Project Documentation/research_flow.md`, `docs/research_flow.md`
- How-to run: `src/Project Documentation/how to run this.md`

## Notes

- Pricing is model-agnostic; the env vars apply to whatever model is used. We set them for Sonnet 4 pricing as requested.
- You can disable dev-mode by unsetting `DEEPAGENTS_DEV_MODE` or setting it to `0` and removing explicit caps.
