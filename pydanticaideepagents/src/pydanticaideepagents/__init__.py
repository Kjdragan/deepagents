"""Pydantic AI Deep Agents - A Python-centric deep agent framework.

This package provides the same Deep Agent functionality as the LangGraph version
but built on Pydantic AI for better Python integration, type safety, and
reduced abstraction while preserving all sophisticated prompting.
"""

from typing import List, Dict, Any, Optional, Callable, Union

# Import core components that don't require pydantic_ai
from .dependencies import DeepAgentDependencies
from .mock_filesystem import MockFileSystem
from .todo_manager import TodoManager, Todo

# Conditionally import components that require pydantic_ai
try:
    from pydantic_ai.models import Model
    from .deep_agent import DeepAgent, SubAgentConfig
    _PYDANTIC_AI_AVAILABLE = True
except ImportError:
    _PYDANTIC_AI_AVAILABLE = False
    Model = None
    DeepAgent = None
    SubAgentConfig = None

__version__ = "0.1.0"
__all__ = [
    "create_deep_agent",
    "DeepAgent", 
    "SubAgentConfig",
    "DeepAgentDependencies",
    "MockFileSystem",
    "TodoManager", 
    "Todo"
]


def create_deep_agent(
    tools: List[Callable],
    instructions: str,
    model: Optional[Model] = None,
    subagents: Optional[List[Dict[str, Any]]] = None,
    agent_id: Optional[str] = None,
    enable_tracing: bool = False,
    project_name: str = "pydantic-deepagents"
) -> DeepAgent:
    """Create a deep agent with the same interface as the LangGraph version.
    
    Raises ImportError if pydantic_ai is not available.
    
    This function provides a drop-in replacement for the LangGraph create_deep_agent
    function, maintaining the same API while leveraging Pydantic AI's architecture.
    
    Args:
        tools: List of additional tools the agent should have access to
        instructions: Custom instructions that will be part of the system prompt
        model: The model to use (defaults to claude-sonnet-4-20250514)
        subagents: Optional list of sub-agent configurations with keys:
                  - name: str
                  - description: str  
                  - prompt: str
                  - tools: Optional[List[str]]
        agent_id: Unique identifier for the agent (auto-generated if None)
        enable_tracing: Whether to enable tracing (placeholder for future)
        project_name: Project name for tracing
        
    Returns:
        DeepAgent instance ready to run with the same functionality as LangGraph
        
    Example:
        ```python
        from pydanticaideepagents import create_deep_agent
        
        def my_tool(ctx, query: str) -> str:
            return f"Result for {query}"
        
        agent = create_deep_agent(
            tools=[my_tool],
            instructions="You are an expert researcher."
        )
        
        result = agent.run_sync("What is machine learning?")
        print(result.output)
        ```
    """
    if not _PYDANTIC_AI_AVAILABLE:
        raise ImportError("pydantic_ai is required to create deep agents. Please install it with: pip install pydantic-ai")
    
    # Convert subagents dict format to SubAgentConfig objects
    subagent_configs = []
    if subagents:
        for subagent_dict in subagents:
            config = SubAgentConfig(
                name=subagent_dict["name"],
                description=subagent_dict["description"], 
                prompt=subagent_dict["prompt"],
                tools=subagent_dict.get("tools")
            )
            subagent_configs.append(config)
    
    return DeepAgent(
        tools=tools,
        instructions=instructions,
        model=model,
        subagents=subagent_configs,
        agent_id=agent_id,
        enable_tracing=enable_tracing,
        project_name=project_name
    )