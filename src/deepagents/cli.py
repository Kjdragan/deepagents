import os
import sys
from enum import Enum
import typer
from typing import Optional
from dotenv import load_dotenv, find_dotenv
from langchain_anthropic import ChatAnthropic

from deepagents import create_deep_agent
from deepagents.tracing import initialize_tracing, is_tracing_enabled, get_trace_url, get_arize_dashboard_url
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


class ModelChoice(str, Enum):
    sonnet4 = "sonnet4"  # claude-sonnet-4-20250514
    opus = "opus"        # claude-3-opus-20240229
    haiku = "haiku"      # claude-3-haiku-20240307


def _resolve_model(model: Optional[ModelChoice], model_name: Optional[str], max_tokens: int) -> Optional[ChatAnthropic]:
    """Return a ChatAnthropic instance based on selector or explicit name, or None to use default."""
    if model_name:
        return ChatAnthropic(model_name=model_name, max_tokens=max_tokens)
    if model == ModelChoice.sonnet4:
        return ChatAnthropic(model_name="claude-sonnet-4-20250514", max_tokens=max_tokens)
    if model == ModelChoice.opus:
        return ChatAnthropic(model_name="claude-3-opus-20240229", max_tokens=max_tokens)
    if model == ModelChoice.haiku:
        return ChatAnthropic(model_name="claude-3-haiku-20240307", max_tokens=max_tokens)
    return None


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
    model: Optional[ModelChoice] = typer.Option(None, case_sensitive=False, help="Select Anthropic model preset: sonnet4 | opus | haiku"),
    model_name: Optional[str] = typer.Option(None, help="Explicit Anthropic model name (overrides --model), e.g., claude-3-opus-20240229"),
    max_tokens: int = typer.Option(64000, help="Max tokens for the LLM."),
    enable_tracing: bool = typer.Option(True, help="Enable Phoenix/Arize tracing for observability."),
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

    # Initialize tracing if enabled
    project_name = "deepagents-cli"
    if enable_tracing:
        tracing_success = initialize_tracing(project_name=project_name)
        if tracing_success:
            typer.secho("✓ Phoenix/Arize tracing enabled", fg=typer.colors.GREEN, err=True)
            
            # Display clickable dashboard link
            dashboard_url = get_arize_dashboard_url(project_name=project_name)
            if dashboard_url:
                typer.secho("🔗 Arize Dashboard:", fg=typer.colors.BRIGHT_CYAN, err=True)
                typer.secho(f"   {dashboard_url}", fg=typer.colors.BLUE, err=True)
                typer.secho("   ↑ Click to view live traces and analytics", fg=typer.colors.BRIGHT_BLACK, err=True)
            else:
                trace_url = get_trace_url()
                if trace_url:
                    typer.secho(f"  View traces at: {trace_url}", fg=typer.colors.BLUE, err=True)
        else:
            typer.secho("⚠ Tracing initialization failed (check ARIZE_SPACE_ID)", fg=typer.colors.YELLOW, err=True)

    model_instance = _resolve_model(model, model_name, max_tokens)
    agent = create_deep_agent(
        [internet_search], 
        instructions, 
        model=model_instance,
        enable_tracing=enable_tracing,
        project_name=project_name
    )

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
    
    # Display dashboard link again after completion
    if enable_tracing and is_tracing_enabled():
        dashboard_url = get_arize_dashboard_url(project_name=project_name)
        if dashboard_url:
            typer.secho(f"\n📊 Research complete! View traces at:", fg=typer.colors.BRIGHT_GREEN, err=True)
            typer.secho(f"   {dashboard_url}", fg=typer.colors.BLUE, err=True)


@app.command(help="Check Phoenix/Arize tracing configuration and status.")
def tracing_status():
    """Display current tracing configuration and status."""
    typer.secho("Phoenix/Arize Tracing Configuration", fg=typer.colors.BRIGHT_CYAN, bold=True)
    typer.echo("=" * 40)
    
    # Check environment variables
    api_key = os.getenv("ARIZE_API_KEY")
    space_id = os.getenv("ARIZE_SPACE_ID")
    
    if api_key:
        typer.secho("✓ ARIZE_API_KEY: Configured", fg=typer.colors.GREEN)
    else:
        typer.secho("✗ ARIZE_API_KEY: Missing", fg=typer.colors.RED)
        typer.echo("  Set with: export ARIZE_API_KEY=your_api_key")
    
    if space_id and space_id != "your_space_id_here":
        typer.secho("✓ ARIZE_SPACE_ID: Configured", fg=typer.colors.GREEN)
    else:
        typer.secho("✗ ARIZE_SPACE_ID: Missing or not configured", fg=typer.colors.RED)
        typer.echo("  Set with: export ARIZE_SPACE_ID=your_space_id")
        typer.echo("  Find your Space ID in the Arize platform")
    
    # Test tracing initialization
    typer.echo("\nTesting tracing initialization...")
    tracing_success = initialize_tracing(project_name="deepagents-status-test")
    
    if tracing_success:
        typer.secho("✓ Tracing initialization: Success", fg=typer.colors.GREEN)
        dashboard_url = get_arize_dashboard_url()
        if dashboard_url:
            typer.secho(f"✓ Dashboard URL: {dashboard_url}", fg=typer.colors.BLUE)
    else:
        typer.secho("✗ Tracing initialization: Failed", fg=typer.colors.RED)
        typer.echo("  Check your ARIZE_API_KEY and ARIZE_SPACE_ID")
    
    typer.echo("\nFor help with Arize configuration:")
    typer.echo("  - Visit: https://app.arize.com")
    typer.echo("  - Documentation: https://arize.com/docs/ax")


def main() -> None:
    app()
