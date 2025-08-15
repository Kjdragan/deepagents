# Evaluation Plan for DeepAgents (Arize/Phoenix)

This plan describes how to evaluate DeepAgents research runs using Phoenix evals (LLM-as-a-Judge) and log results to Arize for analysis alongside traces.

References:
- LLM-as-a-Judge overview: https://arize.com/docs/phoenix/learn/evaluation/llm-as-a-judge
- Cookbook (prompt optimization with llm_classify): https://arize.com/docs/phoenix/cookbook/prompt-engineering/llm-as-a-judge-prompt-optimization
- Datasets API: https://arize.com/docs/phoenix/sdk-api-reference/rest-api/datasets

## Goals
- Measure task success, instruction following, and output usefulness per run.
- Compare experiments across prompt/model/parameter changes.
- Correlate evaluation outcomes with tracing metrics (latency, tokens, errors).

## Dependencies
Phoenix evals are provided by the OSS Phoenix library (import path `phoenix`). Install:

```bash
pip install arize-phoenix
```

Evaluator LLM requirement (example using OpenAI):

```bash
export OPENAI_API_KEY=...  # for evaluator only
```

Note: You may use Anthropic for the application model while using OpenAI for evaluators. Replace with any supported model in `phoenix.evals` if desired.

## Dataset Schema
Create a tabular dataset (CSV/Parquet or in-memory DataFrame) with at least:
- `run_id` (str): unique per research invocation.
- `input` (str): user goal/task given to the agent.
- `output` (str): final agent answer or synthesized report.
- Optional context:
  - `agent_type` (str): e.g., `main-agent`.
  - `model_name` (str), `model_params` (json/str).
  - `latency_ms` (number), `tokens_total` (number), `cost_usd` (number).
  - `errors` (str) summary if any.
  - `notes` (str): freeform annotations.

Source of truth:
- `examples/research/dump_run.py` writes step-by-step events and final state snapshots to `outputs/`. Parse final state and any saved in-memory files to build rows.

## Evaluators (LLM-as-a-Judge)
Use `phoenix.evals.llm_classify` with natural-language rubrics to obtain labels and (optionally) numerical scores.

Baseline evaluators:
1) Instruction Following
- Prompt: “Does the assistant's final output satisfy the user's stated goal? Answer one of: YES, PARTIAL, NO. Briefly justify.”
- Output: `follow_label` in {YES, PARTIAL, NO}, `follow_reason`.

2) Usefulness/Actionability
- Prompt: “Is the output useful and actionable for the user to proceed? Answer one of: HIGH, MEDIUM, LOW. Briefly justify.”
- Output: `useful_label` in {HIGH, MEDIUM, LOW}, `useful_reason`.

Optional evaluators (future): factuality checks against cited sources, safety style, clarity score.

## Minimal Eval Runner (outline)
This outline shows how to run evals over a DataFrame and attach results.

```python
import pandas as pd
from phoenix.evals import OpenAIModel, llm_classify

# df columns: run_id, input, output (and optional metadata)
df = pd.read_csv("outputs/compiled_runs.csv")

model = OpenAIModel(model="gpt-4o-mini", temperature=0)

follow_rubric = (
    "You are judging whether the assistant's final output satisfies the user's goal.\n"
    "Respond with one of: YES, PARTIAL, NO. Provide a brief justification."
)

useful_rubric = (
    "You are judging whether the output is useful and actionable for the user.\n"
    "Respond with one of: HIGH, MEDIUM, LOW. Provide a brief justification."
)

# Evaluate instruction following
follow = llm_classify(
    model=model,
    inputs=[{"input": r, "output": y} for r, y in zip(df["input"], df["output"])],
    rubric=follow_rubric,
    labels=["YES", "PARTIAL", "NO"],
)

# Evaluate usefulness
useful = llm_classify(
    model=model,
    inputs=[{"input": r, "output": y} for r, y in zip(df["input"], df["output"])],
    rubric=useful_rubric,
    labels=["HIGH", "MEDIUM", "LOW"],
)

# Attach results
out = df.copy()
out["follow_label"] = [r.label for r in follow]
out["follow_reason"] = [r.explanation for r in follow]
out["useful_label"] = [r.label for r in useful]
out["useful_reason"] = [r.explanation for r in useful]

out.to_csv("outputs/eval_results.csv", index=False)
print("Wrote outputs/eval_results.csv")
```

## Logging Results to Arize (Datasets/Experiments)
- Create or upsert a Dataset named `deepagents-evals` via Arize Phoenix REST (see Datasets API) or through the Arize UI.
- Upload `eval_results.csv` as a new dataset version or log rows as examples with metadata.
- Optionally, create Experiments by tagging runs (e.g., `prompt=v2`, `model=claude-sonnet`) and compare `follow_label`/`useful_label` distributions.

## Correlate with Traces
- In Arize, use filters on `run_id` to connect eval rows to traces.
- Dashboards (see `docs/phoenix_dashboards.md`): add widgets slicing by `follow_label`/`useful_label` to observe latency/cost trade-offs vs. quality.

## Next Steps
- Implement an `examples/research/eval_run.py` that builds the DataFrame from `outputs/` runs and executes the above evals, then uploads to Arize (TODO t9).
- Optionally add more evaluators and numeric scoring (e.g., map YES/PARTIAL/NO → 1/0.5/0 for aggregate charts).
- Schedule periodic evals for regression testing after prompt/model changes.
