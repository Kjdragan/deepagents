"""Phoenix/Arize tracing integration for DeepAgents.

This module provides LangGraph-based tracing through LangChain instrumentation,
automatically capturing all agent workflows, tool usage, and model interactions.
"""

import os
import logging
from typing import Optional
from openinference.instrumentation.langchain import LangChainInstrumentor
import arize.otel

logger = logging.getLogger(__name__)

_tracing_initialized = False

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