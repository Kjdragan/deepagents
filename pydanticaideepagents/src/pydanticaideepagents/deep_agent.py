"""Main DeepAgent implementation for Pydantic AI.

This module provides the core Deep Agent functionality with dynamic context injection,
preserving all sophisticated prompting from the LangGraph version while leveraging
Pydantic AI's architecture for better Python-centric agent development.
"""

from typing import List, Dict, Any, Optional, Callable, Union
from datetime import datetime
import uuid
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import AnthropicModel, Model
from dataclasses import dataclass

from .dependencies import DeepAgentDependencies
from .tools import (
    ls_tool, 
    read_file_tool, 
    write_file_tool, 
    edit_file_tool, 
    write_todos_tool
)


@dataclass
class SubAgentConfig:
    """Configuration for a sub-agent."""
    name: str
    description: str
    prompt: str
    tools: Optional[List[str]] = None


class DeepAgent:
    """Pydantic AI implementation of Deep Agent with exact LangGraph functionality.
    
    This class preserves all the sophisticated prompting and agent behavior
    from the LangGraph version while leveraging Pydantic AI's dependency
    injection and state management capabilities.
    """
    
    def __init__(
        self,
        tools: List[Callable],
        instructions: str,
        model: Optional[Model] = None,
        subagents: Optional[List[SubAgentConfig]] = None,
        agent_id: Optional[str] = None,
        enable_tracing: bool = False,
        project_name: str = "pydantic-deepagents"
    ):
        """Initialize the Deep Agent.
        
        Args:
            tools: Additional tools the agent should have access to
            instructions: Custom instructions for the agent
            model: Model to use (defaults to Claude Sonnet 4)
            subagents: List of sub-agent configurations
            agent_id: Unique identifier for the agent
            enable_tracing: Whether to enable tracing (placeholder for future)
            project_name: Project name for tracing
        """
        self.tools = tools or []
        self.instructions = instructions
        self.model = model or self._get_default_model()
        self.subagents = subagents or []
        self.agent_id = agent_id or f"agent-{str(uuid.uuid4())[:8]}"
        self.enable_tracing = enable_tracing
        self.project_name = project_name
        
        # Create the main agent with dynamic system prompt
        self.agent = self._create_agent()
        
        # Create sub-agents if specified
        self.sub_agents = self._create_sub_agents()
    
    def _get_default_model(self) -> Model:
        """Get the default Claude Sonnet 4 model."""
        return AnthropicModel('claude-sonnet-4-20250514')
    
    def _get_base_prompt(self) -> str:
        """Get the base prompt that's identical to LangGraph version."""
        return """You have access to a number of standard tools

## `write_todos`

You have access to the `write_todos` tools to help you manage and plan tasks. Use these tools VERY frequently to ensure that you are tracking your tasks and giving the user visibility into your progress.
These tools are also EXTREMELY helpful for planning tasks, and for breaking down larger complex tasks into smaller steps. If you do not use this tool when planning, you may forget to do important tasks - and that is unacceptable.

It is critical that you mark todos as completed as soon as you are done with a task. Do not batch up multiple tasks before marking them as completed.

## `task`

- When doing web search, prefer to use the `task` tool in order to reduce context usage."""
    
    def _get_dynamic_system_prompt(self, ctx: RunContext[DeepAgentDependencies]) -> str:
        """Generate dynamic system prompt with current context.
        
        This method implements dynamic context injection, adapting the system
        prompt based on current state, similar to LangGraph's approach but
        leveraging Pydantic AI's RunContext.
        """
        # Compute current datetime and inject into prompt
        now_human = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
        date_prefix = (
            f"You must treat the current local date/time as: {now_human}. "
            "Use the most recent, reliable information available.\n\n"
        )
        
        # Build the complete system prompt
        system_prompt = date_prefix + self.instructions + self._get_base_prompt()
        
        # Add context about available files if any exist
        files = ctx.deps.get_file_system().ls()
        if files:
            file_context = f"\n\nCurrently available files in the workspace:\n"
            for file_name in files[:10]:  # Limit to avoid context bloat
                file_context += f"- {file_name}\n"
            if len(files) > 10:
                file_context += f"... and {len(files) - 10} more files\n"
            system_prompt += file_context
        
        # Add current todos context
        todos = ctx.deps.get_todo_manager().get_todos()
        if todos:
            todo_context = f"\n\nCurrent todo list status:\n"
            for todo in todos[:5]:  # Limit to avoid context bloat
                todo_context += f"- [{todo.status}] {todo.content}\n"
            if len(todos) > 5:
                todo_context += f"... and {len(todos) - 5} more todos\n"
            system_prompt += todo_context
        
        return system_prompt
    
    def _create_agent(self) -> Agent[DeepAgentDependencies, str]:
        """Create the main Pydantic AI agent with all tools."""
        
        # Create agent with dynamic system prompt
        agent = Agent(
            self.model,
            deps_type=DeepAgentDependencies,
            system_prompt=self._get_dynamic_system_prompt,
        )
        
        # Register built-in tools
        agent.tool(ls_tool)
        agent.tool(read_file_tool)
        agent.tool(write_file_tool)
        agent.tool(edit_file_tool) 
        agent.tool(write_todos_tool)
        
        # Register additional tools
        for tool in self.tools:
            agent.tool(tool)
        
        # Register task tool for sub-agents if subagents exist
        if self.subagents:
            agent.tool(self._create_task_tool())
        
        return agent
    
    def _create_sub_agents(self) -> Dict[str, Agent[DeepAgentDependencies, str]]:
        """Create sub-agents with their specific configurations."""
        sub_agents = {}
        
        # Always create general-purpose sub-agent (like LangGraph version)
        general_agent = Agent(
            self.model,
            deps_type=DeepAgentDependencies,
            system_prompt=lambda ctx: self._get_dynamic_system_prompt(ctx)
        )
        
        # Register tools for general-purpose agent
        general_agent.tool(ls_tool)
        general_agent.tool(read_file_tool)
        general_agent.tool(write_file_tool)
        general_agent.tool(edit_file_tool)
        general_agent.tool(write_todos_tool)
        for tool in self.tools:
            general_agent.tool(tool)
        
        sub_agents["general-purpose"] = general_agent
        
        # Create custom sub-agents
        for subagent_config in self.subagents:
            def make_subagent_prompt(config):
                def subagent_prompt(ctx: RunContext[DeepAgentDependencies]) -> str:
                    now_human = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
                    date_prefix = (
                        f"You must treat the current local date/time as: {now_human}. "
                        "Use the most recent, reliable information available.\n\n"
                    )
                    return date_prefix + config.prompt
                return subagent_prompt
            
            subagent = Agent(
                self.model,
                deps_type=DeepAgentDependencies,
                system_prompt=make_subagent_prompt(subagent_config)
            )
            
            # Register tools based on configuration
            if subagent_config.tools:
                # Register only specified tools
                tool_map = {tool.__name__: tool for tool in self.tools}
                tool_map.update({
                    'ls_tool': ls_tool,
                    'read_file_tool': read_file_tool,
                    'write_file_tool': write_file_tool,
                    'edit_file_tool': edit_file_tool,
                    'write_todos_tool': write_todos_tool
                })
                
                for tool_name in subagent_config.tools:
                    if tool_name in tool_map:
                        subagent.tool(tool_map[tool_name])
            else:
                # Register all tools (default behavior)
                subagent.tool(ls_tool)
                subagent.tool(read_file_tool)
                subagent.tool(write_file_tool)
                subagent.tool(edit_file_tool)
                subagent.tool(write_todos_tool)
                for tool in self.tools:
                    subagent.tool(tool)
            
            sub_agents[subagent_config.name] = subagent
        
        return sub_agents
    
    def _create_task_tool(self):
        """Create the task tool for sub-agent delegation."""
        
        def task_tool(
            ctx: RunContext[DeepAgentDependencies],
            description: str,
            subagent_type: str
        ) -> str:
            """Launch a new agent to handle complex, multi-step tasks autonomously.

            Available agent types and the tools they have access to:
            - general-purpose: General-purpose agent for researching complex questions, searching for files and content, and executing multi-step tasks. When you are searching for a keyword or file and are not confident that you will find the right match in the first few tries use this agent to perform the search for you. (Tools: *)
            """ + ("".join([f"- {sa.name}: {sa.description}" for sa in self.subagents])) + """

            When using the Task tool, you must specify a subagent_type parameter to select which agent type to use.

            Usage notes:
            1. Launch multiple agents concurrently whenever possible, to maximize performance
            2. When the agent is done, it will return a single message back to you
            3. Each agent invocation is stateless
            4. The agent's outputs should generally be trusted
            5. Clearly tell the agent whether you expect it to create content, perform analysis, or just do research

            Args:
                ctx: Pydantic AI run context with dependencies
                description: Description of the task for the sub-agent
                subagent_type: Type of sub-agent to use
                
            Returns:
                Result from the sub-agent
            """
            if subagent_type not in self.sub_agents:
                available_types = list(self.sub_agents.keys())
                return f"Error: invoked agent of type {subagent_type}, the only allowed types are {available_types}"
            
            # Get the sub-agent
            sub_agent = self.sub_agents[subagent_type]
            
            # Run the sub-agent with the same dependencies (shared state)
            try:
                result = sub_agent.run_sync(description, deps=ctx.deps)
                return result.output
            except Exception as e:
                return f"Error running sub-agent: {str(e)}"
        
        return task_tool
    
    async def run_async(
        self, 
        user_input: str, 
        initial_files: Optional[Dict[str, str]] = None,
        deps: Optional[DeepAgentDependencies] = None
    ) -> Any:
        """Run the agent asynchronously.
        
        Args:
            user_input: The user's input/query
            initial_files: Optional initial files to load into the filesystem
            deps: Optional pre-configured dependencies
            
        Returns:
            Agent response
        """
        if deps is None:
            deps = DeepAgentDependencies()
        
        if initial_files:
            deps.initialize_with_files(initial_files)
        
        # Set agent metadata
        deps.set_metadata("agent_id", self.agent_id)
        deps.set_metadata("agent_type", "main-agent")
        
        result = await self.agent.run(user_input, deps=deps)
        return result
    
    def run_sync(
        self, 
        user_input: str, 
        initial_files: Optional[Dict[str, str]] = None,
        deps: Optional[DeepAgentDependencies] = None
    ) -> Any:
        """Run the agent synchronously.
        
        Args:
            user_input: The user's input/query
            initial_files: Optional initial files to load into the filesystem
            deps: Optional pre-configured dependencies
            
        Returns:
            Agent response
        """
        if deps is None:
            deps = DeepAgentDependencies()
        
        if initial_files:
            deps.initialize_with_files(initial_files)
        
        # Set agent metadata
        deps.set_metadata("agent_id", self.agent_id)
        deps.set_metadata("agent_type", "main-agent")
        
        result = self.agent.run_sync(user_input, deps=deps)
        return result
    
    def get_state_snapshot(self, deps: DeepAgentDependencies) -> Dict[str, Any]:
        """Get a snapshot of the current agent state.
        
        Args:
            deps: The dependencies containing the current state
            
        Returns:
            Dictionary with state information
        """
        return deps.get_state_snapshot()