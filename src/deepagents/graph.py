from deepagents.sub_agent import _create_task_tool, SubAgent
from deepagents.model import get_default_model
from deepagents.tools import write_todos, write_file, read_file, ls, edit_file
from deepagents.state import DeepAgentState
from deepagents.tracing import initialize_tracing, log_agent_invocation, configure_agent_metadata
from typing import Sequence, Union, Callable, Any, TypeVar, Type, Optional
from langchain_core.tools import BaseTool
from langchain_core.language_models import LanguageModelLike
import uuid

from langgraph.prebuilt import create_react_agent

StateSchema = TypeVar("StateSchema", bound=DeepAgentState)
StateSchemaType = Type[StateSchema]

base_prompt = """You have access to a number of standard tools

## `write_todos`

You have access to the `write_todos` tools to help you manage and plan tasks. Use these tools VERY frequently to ensure that you are tracking your tasks and giving the user visibility into your progress.
These tools are also EXTREMELY helpful for planning tasks, and for breaking down larger complex tasks into smaller steps. If you do not use this tool when planning, you may forget to do important tasks - and that is unacceptable.

It is critical that you mark todos as completed as soon as you are done with a task. Do not batch up multiple tasks before marking them as completed.
## `task`

- When doing web search, prefer to use the `task` tool in order to reduce context usage."""


def create_deep_agent(
    tools: Sequence[Union[BaseTool, Callable, dict[str, Any]]],
    instructions: str,
    model: Optional[Union[str, LanguageModelLike]] = None,
    subagents: list[SubAgent] = None,
    state_schema: Optional[StateSchemaType] = None,
    enable_tracing: bool = True,
    project_name: str = "deepagents",
    agent_id: Optional[str] = None,
):
    """Create a deep agent with optional Phoenix/Arize tracing.

    This agent will by default have access to a tool to write todos (write_todos),
    and then four file editing tools: write_file, ls, read_file, edit_file.

    Args:
        tools: The additional tools the agent should have access to.
        instructions: The additional instructions the agent should have. Will go in
            the system prompt.
        model: The model to use.
        subagents: The subagents to use. Each subagent should be a dictionary with the
            following keys:
                - `name`
                - `description` (used by the main agent to decide whether to call the sub agent)
                - `prompt` (used as the system prompt in the subagent)
                - (optional) `tools`
        state_schema: The schema of the deep agent. Should subclass from DeepAgentState
        enable_tracing: Whether to initialize Phoenix/Arize tracing (default: True)
        project_name: Project name for tracing (default: "deepagents")
        agent_id: Unique agent identifier for tracing (auto-generated if None)
    """
    # Initialize tracing if enabled
    if enable_tracing:
        initialize_tracing(project_name=project_name, disable_tracing=not enable_tracing)
    
    # Generate agent ID for tracing
    if agent_id is None:
        agent_id = f"agent-{str(uuid.uuid4())[:8]}"
    
    # Log agent creation
    if enable_tracing:
        log_agent_invocation(agent_id, "main-agent")
    
    prompt = instructions + base_prompt
    built_in_tools = [write_todos, write_file, read_file, ls, edit_file]
    if model is None:
        model = get_default_model()
    state_schema = state_schema or DeepAgentState
    task_tool = _create_task_tool(
        list(tools) + built_in_tools,
        instructions,
        subagents or [],
        model,
        state_schema,
        parent_agent_id=agent_id if enable_tracing else None
    )
    all_tools = built_in_tools + list(tools) + [task_tool]
    agent = create_react_agent(
        model,
        prompt=prompt,
        tools=all_tools,
        state_schema=state_schema,
    )

    # Attach tracing metadata to the main agent for Arize multi-agent visualization
    if enable_tracing:
        metadata = configure_agent_metadata(agent_id)
        metadata["agent.type"] = "main-agent"
        agent = agent.with_config(metadata=metadata)

    return agent
