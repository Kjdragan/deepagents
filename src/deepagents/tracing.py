"""Phoenix/Arize tracing integration for DeepAgents.

This module provides LangGraph-based tracing through LangChain instrumentation,
automatically capturing all agent workflows, tool usage, and model interactions.
"""

import os
import logging
from typing import Optional
from openinference.instrumentation.langchain import LangChainInstrumentor
from opentelemetry import trace
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult
import arize.otel

logger = logging.getLogger(__name__)

_tracing_initialized = False
_callback_handler_singleton: Optional["_OTelSpanEnricher"] = None


class _OTelSpanEnricher(BaseCallbackHandler):
    """LangChain callback that enriches the current OTEL span with useful attributes.

    Records token usage if provided by the LLM and annotates errors on failure.
    """

    def _set_attr(self, key: str, value):
        try:
            span = trace.get_current_span()
            if span is not None:
                span.set_attribute(key, value)
        except Exception:
            pass

    def _maybe_cost(self, input_tokens: Optional[int], output_tokens: Optional[int]):
        """Optionally compute cost if pricing env vars are provided.

        Env vars:
        - LLM_PRICE_INPUT_PER_1K
        - LLM_PRICE_OUTPUT_PER_1K
        """
        try:
            pin = float(os.getenv("LLM_PRICE_INPUT_PER_1K", "0") or 0)
            pout = float(os.getenv("LLM_PRICE_OUTPUT_PER_1K", "0") or 0)
            if pin == 0 and pout == 0:
                return None
            cost = 0.0
            if input_tokens:
                cost += (input_tokens / 1000.0) * pin
            if output_tokens:
                cost += (output_tokens / 1000.0) * pout
            return round(cost, 6)
        except Exception:
            return None

    # LLM success path
    def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        try:
            # Attach run/session IDs if available (ensures grouping in dashboards)
            try:
                run_id = os.getenv("DEEPAGENTS_RUN_ID")
                session_id = os.getenv("DEEPAGENTS_SESSION_ID")
                if run_id:
                    self._set_attr("run.id", run_id)
                if session_id:
                    self._set_attr("session.id", session_id)
            except Exception:
                pass

            usage = {}
            if response.llm_output and isinstance(response.llm_output, dict):
                usage = response.llm_output.get("token_usage") or response.llm_output.get("usage") or {}
            # Fallback: look into generation info
            if not usage and response.generations:
                gi = response.generations[0][0].generation_info or {}
                usage = gi.get("token_usage") or gi.get("usage") or {}

            input_tokens = usage.get("prompt_tokens") or usage.get("input_tokens")
            output_tokens = usage.get("completion_tokens") or usage.get("output_tokens")
            total_tokens = usage.get("total_tokens")
            if total_tokens is None and (input_tokens is not None or output_tokens is not None):
                total_tokens = (input_tokens or 0) + (output_tokens or 0)

            if input_tokens is not None:
                self._set_attr("llm.input_tokens", int(input_tokens))
            if output_tokens is not None:
                self._set_attr("llm.output_tokens", int(output_tokens))
            if total_tokens is not None:
                self._set_attr("llm.total_tokens", int(total_tokens))

            cost = self._maybe_cost(input_tokens, output_tokens)
            if cost is not None:
                self._set_attr("llm.cost_usd", cost)
        except Exception:
            # Never fail the run because of telemetry
            pass

    # Error paths
    def on_llm_error(self, error: BaseException, **kwargs) -> None:
        try:
            span = trace.get_current_span()
            if span is not None:
                span.set_attribute("error", True)
                span.set_attribute("error.type", error.__class__.__name__)
                span.set_attribute("error.message", str(error)[:512])
                # Ensure run/session context present on error spans
                try:
                    run_id = os.getenv("DEEPAGENTS_RUN_ID")
                    session_id = os.getenv("DEEPAGENTS_SESSION_ID")
                    if run_id:
                        span.set_attribute("run.id", run_id)
                    if session_id:
                        span.set_attribute("session.id", session_id)
                except Exception:
                    pass
                try:
                    span.record_exception(error)
                except Exception:
                    pass
        except Exception:
            pass

    def on_chain_error(self, error: BaseException, **kwargs) -> None:
        self.on_llm_error(error, **kwargs)

    def on_tool_error(self, error: BaseException, **kwargs) -> None:
        self.on_llm_error(error, **kwargs)


def get_tracing_callback_handler() -> BaseCallbackHandler:
    """Return a singleton callback handler for enriching spans with usage and errors."""
    global _callback_handler_singleton
    if _callback_handler_singleton is None:
        _callback_handler_singleton = _OTelSpanEnricher()
    return _callback_handler_singleton

def initialize_tracing(
    project_name: str = "deepagents",
    auto_instrument: bool = True,
    disable_tracing: bool = False
) -> bool:
    """Initialize Phoenix/Arize tracing for DeepAgents.
    
    This function sets up LangGraph/LangChain tracing through the Arize cloud platform.
    It automatically instruments all LangGraph agents and underlying model calls.
    
    Args:
        project_name: Name of the project in Arize (default: "deepagents")
        auto_instrument: Whether to automatically instrument LangChain (default: True)
        disable_tracing: Set to True to skip tracing initialization (default: False)
        
    Returns:
        bool: True if tracing was successfully initialized, False otherwise
    """
    global _tracing_initialized
    
    if _tracing_initialized:
        logger.debug("Tracing already initialized")
        return True
        
    if disable_tracing:
        logger.info("Tracing disabled by configuration")
        return False
    
    try:
        # Check required environment variables
        api_key = os.getenv("ARIZE_API_KEY")
        space_id = os.getenv("ARIZE_SPACE_ID")
        
        if not api_key:
            logger.warning("ARIZE_API_KEY not found in environment. Tracing disabled.")
            return False
            
        if not space_id or space_id == "your_space_id_here":
            logger.warning("ARIZE_SPACE_ID not configured. Please set your Space ID in .env file.")
            return False
        
        # Initialize Arize OTEL integration
        logger.info(f"Initializing Arize tracing for project: {project_name}")
        arize.otel.register(
            space_id=space_id,
            api_key=api_key,
            project_name=project_name,
        )
        
        # Instrument LangChain (covers LangGraph automatically)
        if auto_instrument:
            logger.info("Instrumenting LangChain/LangGraph for automatic tracing")
            LangChainInstrumentor().instrument()
        
        _tracing_initialized = True
        logger.info("Phoenix/Arize tracing successfully initialized")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize tracing: {e}")
        return False

def is_tracing_enabled() -> bool:
    """Check if tracing has been initialized and is active.
    
    Returns:
        bool: True if tracing is enabled and initialized
    """
    return _tracing_initialized

def get_trace_url() -> Optional[str]:
    """Get the Arize trace URL for the current session.
    
    Returns:
        Optional[str]: URL to view traces in Arize, or None if not available
    """
    if not _tracing_initialized:
        return None
        
    space_id = os.getenv("ARIZE_SPACE_ID")
    if space_id and space_id != "your_space_id_here":
        return f"https://app.arize.com/spaces/{space_id}/phoenix"
    return None

def get_arize_dashboard_url(project_name: Optional[str] = None) -> Optional[str]:
    """Get the Arize dashboard URL for viewing traces and analytics.
    
    Args:
        project_name: Optional project name to link directly to project view
        
    Returns:
        Optional[str]: URL to Arize dashboard, or None if not configured
    """
    space_id = os.getenv("ARIZE_SPACE_ID")
    if not space_id or space_id == "your_space_id_here":
        return None
    
    # Use a generic space-centric URL for Phoenix that does not depend on organization pathing
    # This will redirect appropriately for the authenticated user/org
    return f"https://app.arize.com/spaces/{space_id}/phoenix"

def configure_agent_metadata(agent_id: str, parent_id: Optional[str] = None) -> dict:
    """Configure agent metadata for proper hierarchy tracking.
    
    Args:
        agent_id: Unique identifier for the agent
        parent_id: Parent agent ID for sub-agents (optional)
        
    Returns:
        dict: Metadata configuration for the agent
    """
    metadata = {
        "graph.node.id": agent_id,
    }
    
    if parent_id:
        metadata["graph.node.parent_id"] = parent_id
        
    return metadata

def log_agent_invocation(agent_id: str, agent_type: str, parent_id: Optional[str] = None):
    """Log agent invocation for debugging and monitoring.
    
    Args:
        agent_id: Unique identifier for the agent
        agent_type: Type of agent (e.g., "main-agent", "research-agent", "critique-agent")
        parent_id: Parent agent ID for sub-agents (optional)
    """
    if not _tracing_initialized:
        return
        
    log_msg = f"Agent invocation: {agent_type} (ID: {agent_id})"
    if parent_id:
        log_msg += f" [Parent: {parent_id}]"
        
    logger.info(log_msg)