import argparse
import csv
import json
import os
import re
from pathlib import Path
from typing import Any, List, Dict, Optional

# This script compiles DeepAgents run snapshots produced by
# `examples/research/dump_run.py` into a CSV and optionally runs
# Phoenix LLM-as-a-Judge evaluations if `phoenix` is installed.
# It writes results to `outputs/compiled_runs.csv` and
# `outputs/eval_results.csv` (if evals are run).


def _safe_get(d: dict, key: str, default=None):
    try:
        return d.get(key, default)
    except Exception:
        return default


def _extract_messages(state: dict) -> List[dict]:
    msgs = _safe_get(state, "messages", [])
    # Ensure list of dict-like entries
    out: List[dict] = []
    for m in msgs or []:
        if isinstance(m, dict):
            out.append(m)
        else:
            # objects from LC were converted in dump to {role, content, ...}
            try:
                out.append({
                    "role": getattr(m, "type", getattr(m, "role", "")),
                    "content": getattr(m, "content", ""),
                })
            except Exception:
                pass
    return out


ess_ts_re = re.compile(r"run_state_(\d{8}_\d{6})\.json$")


def _guess_ts_and_run_id(path: Path) -> str:
    m = ess_ts_re.search(path.name)
    if m:
        return m.group(1)
    return path.stem


def _first_user_content(messages: List[dict]) -> Optional[str]:
    for m in messages:
        role = (m.get("role") or "").lower()
        # Some runs serialize the initial human message with role="human"
        if role in ("user", "human"):
            return m.get("content")
    return None


def _final_assistant_content(messages: List[dict]) -> Optional[str]:
    for m in reversed(messages):
        role = (m.get("role") or "").lower()
        if role in ("assistant", "ai"):
            return m.get("content")
    # fallback: last message content
    if messages:
        return messages[-1].get("content")
    return None


def compile_runs(outputs_dir: Path) -> Path:
    outputs_dir.mkdir(parents=True, exist_ok=True)
    rows: List[Dict[str, Any]] = []

    for path in sorted(outputs_dir.glob("run_state_*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        ts = _guess_ts_and_run_id(path)
        msgs = _extract_messages(data)
        input_text = _first_user_content(msgs) or ""
        output_text = _final_assistant_content(msgs) or ""
        summary = _safe_get(data, "summary", {}) or {}
        files = _safe_get(data, "files", {}) or {}

        rows.append({
            "run_id": ts,
            "ts": ts,
            "input": input_text,
            "output": output_text,
            "message_count": summary.get("message_count"),
            "todo_count": summary.get("todo_count"),
            "file_keys": ";".join((files or {}).keys()),
        })

    out_csv = outputs_dir / "compiled_runs.csv"
    if rows:
        fieldnames = list(rows[0].keys())
        with out_csv.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for r in rows:
                w.writerow(r)
    else:
        # Create empty CSV with header
        fieldnames = ["run_id", "ts", "input", "output", "message_count", "todo_count", "file_keys"]
        with out_csv.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()

    return out_csv


def maybe_run_evals(outputs_dir: Path, compiled_csv: Path, model_name: str) -> Optional[Path]:
    try:
        import pandas as pd  # type: ignore
        from phoenix.evals import OpenAIModel, llm_classify  # type: ignore
    except Exception:
        print("phoenix (and pandas) not installed; skipping evals. Install with: pip install arize-phoenix pandas")
        return None

    import pandas as pd  # type: ignore

    df = pd.read_csv(compiled_csv)
    if df.empty:
        print("No rows in compiled CSV; skipping evals.")
        return None

    model = OpenAIModel(model=model_name, temperature=0)

    follow_rubric = (
        "You are judging whether the assistant's final output satisfies the user's goal.\n"
        "Respond with one of: YES, PARTIAL, NO. Provide a brief justification."
    )

    useful_rubric = (
        "You are judging whether the output is useful and actionable for the user.\n"
        "Respond with one of: HIGH, MEDIUM, LOW. Provide a brief justification."
    )

    inputs = [{"input": r, "output": y} for r, y in zip(df["input"], df["output"])]

    try:
        follow = llm_classify(
            model=model,
            inputs=inputs,
            rubric=follow_rubric,
            labels=["YES", "PARTIAL", "NO"],
        )
        useful = llm_classify(
            model=model,
            inputs=inputs,
            rubric=useful_rubric,
            labels=["HIGH", "MEDIUM", "LOW"],
        )
    except Exception as e:
        print(f"Eval execution failed: {e}. Ensure OPENAI_API_KEY is set (or configure phoenix evaluators).")
        return None

    out = df.copy()
    out["follow_label"] = [r.label for r in follow]
    out["follow_reason"] = [r.explanation for r in follow]
    out["useful_label"] = [r.label for r in useful]
    out["useful_reason"] = [r.explanation for r in useful]

    eval_csv = outputs_dir / "eval_results.csv"
    out.to_csv(eval_csv, index=False)
    print(f"Wrote {eval_csv}")
    return eval_csv


def main():
    parser = argparse.ArgumentParser(description="Compile DeepAgents run outputs and optionally run evals.")
    parser.add_argument("--outputs-dir", default=str(Path(__file__).resolve().parents[2] / "outputs"), help="Directory containing run_state_*.json")
    parser.add_argument("--run-evals", action="store_true", help="Run Phoenix LLM-as-a-Judge evals if phoenix is installed")
    parser.add_argument("--evaluator-model", default="gpt-4o-mini", help="Evaluator model name for phoenix.evals OpenAIModel")
    args = parser.parse_args()

    outputs_dir = Path(args.outputs_dir)
    compiled_csv = compile_runs(outputs_dir)
    print(f"Wrote {compiled_csv}")

    if args.run_evals:
        maybe_run_evals(outputs_dir, compiled_csv, args.evaluator_model)


if __name__ == "__main__":
    main()
