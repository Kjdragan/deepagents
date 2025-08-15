"""Main DeepAgent implementation for Pydantic AI.

This module provides the core Deep Agent functionality with dynamic context injection,
preserving all sophisticated prompting from the LangGraph version while leveraging
Pydantic AI's architecture for better Python-centric agent development.
"""

from typing import List, Dict, Any, Optional, Callable, Union
from datetime import datetime
import uuid
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models import Model
from dataclasses import dataclass

from .dependencies import DeepAgentDependencies
from .todo_manager import Todo


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
        
        # Create agent first
        agent = Agent(
            self.model,
            deps_type=DeepAgentDependencies,
            tools=self.tools  # Add user tools via constructor
        )
        
        # Add dynamic system prompt using decorator
        @agent.system_prompt
        def get_system_prompt(ctx: RunContext[DeepAgentDependencies]) -> str:
            return self._get_dynamic_system_prompt(ctx)
        
        # Register built-in tools using decorators
        @agent.tool
        def ls(ctx: RunContext[DeepAgentDependencies]) -> list[str]:
            """List all files in the mock filesystem."""
            return ctx.deps.get_file_system().ls()
        
        @agent.tool
        def read_file(
            ctx: RunContext[DeepAgentDependencies],
            file_path: str,
            offset: int = 0,
            limit: int = 2000
        ) -> str:
            """Read file from the mock filesystem."""
            return ctx.deps.get_file_system().read_file(file_path, offset, limit)
        
        @agent.tool
        def write_file(
            ctx: RunContext[DeepAgentDependencies],
            file_path: str,
            content: str
        ) -> str:
            """Write content to a file in the mock filesystem."""
            return ctx.deps.get_file_system().write_file(file_path, content)
        
        @agent.tool
        def edit_file(
            ctx: RunContext[DeepAgentDependencies],
            file_path: str,
            old_string: str,
            new_string: str,
            replace_all: bool = False
        ) -> str:
            """Edit a file in the mock filesystem."""
            return ctx.deps.get_file_system().edit_file(file_path, old_string, new_string, replace_all)
        
        @agent.tool
        def write_todos(
            ctx: RunContext[DeepAgentDependencies],
            todos: List[Todo]
        ) -> str:
            """Update the todo list for task management."""
            return ctx.deps.get_todo_manager().write_todos(todos)
        
        # Add task tool for sub-agents if needed
        if self.subagents:
            task_tool_func = self._create_task_tool()
            agent.tool(task_tool_func)
        
        return agent
    
    def _create_sub_agents(self) -> Dict[str, Agent[DeepAgentDependencies, str]]:
        """Create sub-agents with their specific configurations."""
        sub_agents = {}
        
        # Always create general-purpose sub-agent (like LangGraph version)
        general_agent = Agent(
            self.model,
            deps_type=DeepAgentDependencies,
            tools=self.tools  # Add user tools via constructor
        )
        
        # Add built-in tools using decorators for general agent
        @general_agent.tool
        def ls(ctx: RunContext[DeepAgentDependencies]) -> list[str]:
            """List all files in the mock filesystem."""
            return ctx.deps.get_file_system().ls()
        
        @general_agent.tool
        def read_file(
            ctx: RunContext[DeepAgentDependencies],
            file_path: str,
            offset: int = 0,
            limit: int = 2000
        ) -> str:
            """Read file from the mock filesystem."""
            return ctx.deps.get_file_system().read_file(file_path, offset, limit)
        
        @general_agent.tool
        def write_file(
            ctx: RunContext[DeepAgentDependencies],
            file_path: str,
            content: str
        ) -> str:
            """Write content to a file in the mock filesystem."""
            return ctx.deps.get_file_system().write_file(file_path, content)
        
        @general_agent.tool
        def edit_file(
            ctx: RunContext[DeepAgentDependencies],
            file_path: str,
            old_string: str,
            new_string: str,
            replace_all: bool = False
        ) -> str:
            """Edit a file in the mock filesystem."""
            return ctx.deps.get_file_system().edit_file(file_path, old_string, new_string, replace_all)
        
        @general_agent.tool
        def write_todos(
            ctx: RunContext[DeepAgentDependencies],
            todos: List[Todo]
        ) -> str:
            """Update the todo list for task management."""
            return ctx.deps.get_todo_manager().write_todos(todos)
        
        # Add dynamic system prompt for general agent
        @general_agent.system_prompt  
        def get_general_system_prompt(ctx: RunContext[DeepAgentDependencies]) -> str:
            return self._get_dynamic_system_prompt(ctx)
        
        sub_agents["general-purpose"] = general_agent
        
        # Create custom sub-agents
        for subagent_config in self.subagents:
            subagent = Agent(
                self.model,
                deps_type=DeepAgentDependencies,
                tools=self.tools  # Add user tools via constructor
            )
            
            # Add built-in tools using decorators for each sub-agent
            # Note: We add all tools for now - tool filtering can be added later if needed
            @subagent.tool
            def ls_sub(ctx: RunContext[DeepAgentDependencies]) -> list[str]:
                """List all files in the mock filesystem."""
                return ctx.deps.get_file_system().ls()
            
            @subagent.tool
            def read_file_sub(
                ctx: RunContext[DeepAgentDependencies],
                file_path: str,
                offset: int = 0,
                limit: int = 2000
            ) -> str:
                """Read file from the mock filesystem."""
                return ctx.deps.get_file_system().read_file(file_path, offset, limit)
            
            @subagent.tool
            def write_file_sub(
                ctx: RunContext[DeepAgentDependencies],
                file_path: str,
                content: str
            ) -> str:
                """Write content to a file in the mock filesystem."""
                return ctx.deps.get_file_system().write_file(file_path, content)
            
            @subagent.tool
            def edit_file_sub(
                ctx: RunContext[DeepAgentDependencies],
                file_path: str,
                old_string: str,
                new_string: str,
                replace_all: bool = False
            ) -> str:
                """Edit a file in the mock filesystem."""
                return ctx.deps.get_file_system().edit_file(file_path, old_string, new_string, replace_all)
            
            @subagent.tool
            def write_todos_sub(
                ctx: RunContext[DeepAgentDependencies],
                todos: List[Todo]
            ) -> str:
                """Update the todo list for task management."""
                return ctx.deps.get_todo_manager().write_todos(todos)
            
            # Add dynamic system prompt for this sub-agent
            def make_subagent_prompt_func(config):
                def subagent_prompt_func(ctx: RunContext[DeepAgentDependencies]) -> str:
                    now_human = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
                    date_prefix = (
                        f"You must treat the current local date/time as: {now_human}. "
                        "Use the most recent, reliable information available.\n\n"
                    )
                    return date_prefix + config.prompt
                return subagent_prompt_func
            
            subagent.system_prompt(make_subagent_prompt_func(subagent_config))
            
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