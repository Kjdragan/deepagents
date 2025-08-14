import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv, find_dotenv
except Exception:
    load_dotenv = None
    find_dotenv = None

# Load .env before importing the agent (so API keys are available at import-time)
if find_dotenv and load_dotenv:
    try:
        dotenv_path = find_dotenv(usecwd=True)
        if dotenv_path:
            load_dotenv(dotenv_path)
    except Exception:
        pass

# Import the existing agent definition so we don't duplicate logic
from examples.research.research_agent import agent  # noqa: E402


def _jsonable(obj: Any) -> Any:
    """Best-effort JSON serializer for LangGraph/LC message objects and others."""
    # LangChain messages: have .type and .content; tool messages may have dict-like
    try:
        from langchain_core.messages import BaseMessage  # type: ignore
    except Exception:
        BaseMessage = tuple()  # type: ignore

    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_jsonable(x) for x in obj]
    if BaseMessage and isinstance(obj, BaseMessage):  # type: ignore
        role = getattr(obj, "type", getattr(obj, "role", obj.__class__.__name__))
        content = getattr(obj, "content", None)
        additional = {}
        for attr in ("tool_calls", "name", "id"):
            if hasattr(obj, attr):
                try:
                    additional[attr] = _jsonable(getattr(obj, attr))
                except Exception:
                    pass
        return {"role": role, "content": content, **additional}
    # Fallback: try to jsonify dataclass-like
    try:
        return json.loads(json.dumps(obj, default=str))
    except Exception:
        return str(obj)


def run_and_dump(question: str) -> Path:
    """
    Run the existing agent with the provided question, dump the final state and any
    generated files (e.g., final_report.md) to outputs/.

    Returns the path to the created state JSON file.
    """
    # Anchor outputs/ at the repository root (two levels up from this file)
    outputs_dir = Path(__file__).resolve().parents[2] / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Invoke the agent to get the final state (messages, files, todos, etc.)
    result = agent.invoke({
        "messages": [{"role": "user", "content": question}],
    })

    # Prepare a pretty-printed, JSON-serializable state snapshot
    state_snapshot = {
        "summary": {
            "message_count": len(result.get("messages", [])) if isinstance(result.get("messages"), list) else None,
            "file_keys": list(result.get("files", {}).keys()) if isinstance(result.get("files"), dict) else [],
            "todo_count": len(result.get("todos", [])) if isinstance(result.get("todos"), list) else 0,
            "available_keys": list(result.keys()),
        },
        "messages": _jsonable(result.get("messages", [])),
        "todos": _jsonable(result.get("todos", [])),
        # include full files mapping for completeness
        "files": _jsonable(result.get("files", {})),
    }

    state_path = outputs_dir / f"run_state_{ts}.json"
    with state_path.open("w", encoding="utf-8") as f:
        json.dump(state_snapshot, f, indent=2, ensure_ascii=False)

    # Write any in-memory files to disk with a timestamped prefix
    files = result.get("files") or {}
    if isinstance(files, dict):
        for fname, content in files.items():
            safe_name = fname.replace("/", "_")
            out_path = outputs_dir / f"{ts}__{safe_name}"
            try:
                with out_path.open("w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                # If binary or other error, write a text note
                with (outputs_dir / f"{ts}__{safe_name}.txt").open("w", encoding="utf-8") as f:
                    f.write(f"[Could not write original content: {e}]\n")
                    f.write(str(content))

    # Fallback: if no report file was created, attempt to write the final assistant
    # message to a markdown file for easier reading.
    wrote_report = False
    if isinstance(files, dict) and files:
        # Heuristically detect a report-like file
        for k in files.keys():
            if "report" in k.lower() and k.lower().endswith((".md", ".txt")):
                wrote_report = True
                break
    if not wrote_report:
        final_msg = None
        try:
            messages = result.get("messages", [])
            if messages:
                # last message content
                final_msg = messages[-1].content if hasattr(messages[-1], "content") else None
                if final_msg is None and isinstance(messages[-1], dict):
                    final_msg = messages[-1].get("content")
        except Exception:
            pass
        if final_msg:
            report_path = outputs_dir / f"{ts}__report.md"
            with report_path.open("w", encoding="utf-8") as f:
                f.write(str(final_msg))

    return state_path


if __name__ == "__main__":
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = "What is LangGraph?"

    path = run_and_dump(question)
    print(f"State written to: {path}")
