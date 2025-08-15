# How to Run This Project

This guide explains how to set up, run, and use the DeepAgents CLI and the research dump runner.

## Prerequisites
- Python 3.11+
- An Anthropic API key
- A Tavily API key
- Either uv (recommended) or pip for dependency management

## Setup
1. Clone the repo and change into it.
2. Create a `.env` file at the repo root with your keys:
   ```env
   ANTHROPIC_API_KEY=sk-ant-...
   TAVILY_API_KEY=tvly-...
   ```
3. Install dependencies and run:
   - With uv (recommended):
     - Run commands directly; uv will resolve and create an environment from `pyproject.toml`/`uv.lock` on demand.
     - Or explicitly set up: `uv sync`
   - With pip:
     ```bash
     pip install -e .
     ```

The CLI will auto-load `.env` (via `python-dotenv`) if present.

## CLI Usage (deepagents)
The CLI is provided via the console script `deepagents` (entry: `deepagents.cli:main`).

Basic research command:
```bash
uv run deepagents research "Your question here"
```

Options:
- `--max-results`: int (default 5) – Max search results to retrieve from Tavily
- `--topic`: one of `general|news|finance` (default `general`)
- `--include-raw-content`: include raw page content in Tavily results (bool, default false)
- `--model`: Anthropic model preset: `sonnet4|opus|haiku`
- `--model-name`: explicit Anthropic model name (overrides `--model`), e.g. `claude-3-opus-20240229`
- `--max-tokens`: LLM output tokens limit (default 64000)

Examples:
```bash
# Default model (Claude Sonnet 4) with a question
uv run deepagents research "What are the latest developments in the Israel war?"

# Use Opus preset and fewer tokens
uv run deepagents research --model opus --max-tokens 4000 "What are the latest developments in the Israel war?"

# Use an explicit model name (Haiku)
uv run deepagents research --model-name claude-3-haiku-20240307 "Summarize key AI safety debates in 2024"

# Adjust search behavior
uv run deepagents research --max-results 8 --topic news "State of quantum computing startups"
```

Notes:
- If using pip instead of uv and you installed with `pip install -e .`, you can call the CLI directly:
  ```bash
  deepagents research "Your question here"
  ```

## Dump Full Run State (streamed events + final state + files)
To deeply inspect what the agent did, use the dump runner:

```bash
uv run python examples/research/dump_run.py "Your question here"
```

Artifacts are saved under `outputs/` with a timestamp prefix:
- `<ts>__events.jsonl`: streamed state snapshots per step (LangGraph `astream(values)`)
- `run_state_<ts>.json`: final state (JSON)
- `run_state_<ts>.txt`: final state (pretty-printed)
- `<ts>__final_report.md` (or other file names): any in-memory files the agent created
- `<ts>__report.md`: fallback – final assistant message if no explicit report file was created

Quick inspection commands:
```bash
# List most recent outputs
ls -lt outputs | head -n 10

# View summary of a run
jq '.summary' outputs/run_state_*.json | head -n 1

# Tail live events while running
tail -f outputs/*__events.jsonl
```

## Troubleshooting
- Missing API keys: the CLI will exit and indicate which environment variable is missing.
- `.env` not loading: ensure the file is at the repo root; the CLI attempts `find_dotenv(usecwd=True)`.
- No outputs are written by the dump runner: nothing streamed yet; verify network/API access, keys, or rerun.
- Default model: `Claude Sonnet 4` (`claude-sonnet-4-20250514`). Use `--model` or `--model-name` to override.

## Key Files
- CLI: `src/deepagents/cli.py`
- Default model: `src/deepagents/model.py`
- Agent definition example: `examples/research/research_agent.py`
- Dump runner: `examples/research/dump_run.py`
- Outputs directory: `outputs/`
