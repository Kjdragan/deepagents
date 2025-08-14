import os
import sys
from enum import Enum
import typer
from typing import Optional
from dotenv import load_dotenv, find_dotenv

from deepagents import create_deep_agent
try:
    from tavily import TavilyClient
except Exception as e:
    TavilyClient = None  # type: ignore


app = typer.Typer(help="DeepAgents CLI")

# Load environment variables from a .env file if present
try:
    _dotenv_path = find_dotenv(usecwd=True)
    if _dotenv_path:
        load_dotenv(_dotenv_path)
except Exception:
    # Don't block CLI if dotenv loading fails; explicit exports still work
    pass


class Topic(str, Enum):
    general = "general"
    news = "news"
    finance = "finance"


def _require_env(var: str) -> str:
    val = os.environ.get(var)
    if not val:
        typer.secho(f"Missing required environment variable: {var}", fg=typer.colors.RED, err=True)
        if var == "TAVILY_API_KEY":
            typer.echo("Export it, e.g.: export TAVILY_API_KEY=...", err=True)
        if var == "ANTHROPIC_API_KEY":
            typer.echo("Export it, e.g.: export ANTHROPIC_API_KEY=...", err=True)
        raise typer.Exit(code=1)
    return val


@app.command(help="Run a quick research query and print a detailed answer.")
def research(
    question: str = typer.Argument(..., help="The research question to answer."),
    max_results: int = typer.Option(5, help="Max search results to retrieve."),
    topic: Topic = typer.Option(Topic.general, help="Search topic vertical."),
    include_raw_content: bool = typer.Option(False, help="Include raw page content from Tavily."),
):
    # Validate environment and dependencies
    if TavilyClient is None:
        typer.secho("tavily-python is not installed. It is required for the research CLI.", fg=typer.colors.RED, err=True)
        typer.echo("Install it with: uv add tavily-python", err=True)
        raise typer.Exit(code=1)

    _require_env("ANTHROPIC_API_KEY")
    tavily_key = _require_env("TAVILY_API_KEY")

    # Initialize Tavily client
    tavily_client = TavilyClient(api_key=tavily_key)

    # Define tool
    def internet_search(
        query: str,
        max_results: int = max_results,
        topic: str = topic.value,
        include_raw_content: bool = include_raw_content,
    ):
        """Run a web search"""
        return tavily_client.search(
            query,
            max_results=max_results,
            include_raw_content=include_raw_content,
            topic=topic,
        )

    # Minimal but effective instructions
    instructions = (
        "You are an expert researcher. Use the internet_search tool to gather information and "
        "return a well-structured, deeply detailed markdown report with headings, analysis, and a Sources section. "
        "Cite sources inline using [Title](URL)."
    )

    agent = create_deep_agent([internet_search], instructions)

    result = agent.invoke({"messages": [{"role": "user", "content": question}]})

    # Try to print the final assistant message
    msg = None
    try:
        messages = result.get("messages", [])
        if messages:
            msg = messages[-1].content
    except Exception:
        pass

    if msg:
        typer.echo(msg)
    else:
        # Fallback: pretty-print the whole result
        typer.echo(str(result))


def main() -> None:
    app()
