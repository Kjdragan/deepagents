# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Package Management and Installation
```bash
# Install in development mode
pip install -e .

# Install with uv (preferred)
uv sync
```

### CLI Usage
```bash
# Run the research CLI
deepagents research "What is LangGraph?"

# With custom parameters
deepagents research "climate change impacts" --max-results 10 --topic news --include-raw-content
```

### Environment Variables
Required environment variables:
- `ANTHROPIC_API_KEY`: Required for all operations
- `TAVILY_API_KEY`: Required for research functionality

Optional: Create `.env` file in project root for automatic loading.

### Testing and Development
No specific test framework is configured. The package uses basic Python packaging with setuptools.

## Architecture

### Core Components

**Deep Agent Framework (`src/deepagents/`)**
- `graph.py`: Main entry point with `create_deep_agent()` function that builds LangGraph-based agents
- `state.py`: Defines `DeepAgentState` extending LangGraph's `AgentState` with todo tracking and mock file system
- `tools.py`: Built-in tools including todo management (`write_todos`) and mock file system operations (`read_file`, `write_file`, `edit_file`, `ls`)
- `sub_agent.py`: Sub-agent spawning system for task delegation and context quarantine
- `model.py`: Default model configuration (Claude Sonnet 4)
- `prompts.py`: Comprehensive system prompts based on Claude Code's approach

**CLI Interface (`src/deepagents/cli.py`)**
- Typer-based CLI with `research` command
- Integrates Tavily search with deep agent framework
- Environment variable validation and error handling

### Key Design Patterns

**Mock File System**: Agents operate on a virtual file system stored in LangGraph state rather than real files, enabling safe parallel execution and isolation.

**Todo Management**: Built-in planning tool that agents use for task breakdown and progress tracking, similar to Claude Code's TodoWrite functionality.

**Sub-agent Architecture**: Agents can spawn specialized sub-agents with custom instructions and tool access for complex task delegation.

**LangGraph Integration**: All agents are standard LangGraph graphs, supporting streaming, human-in-the-loop, and LangGraph Studio integration.

### Custom Agent Creation

Agents are created via `create_deep_agent(tools, instructions, model=None, subagents=None, state_schema=None)`:

- **tools**: List of functions or LangChain tools available to agent and sub-agents
- **instructions**: Custom system prompt additions (combined with built-in prompts)
- **subagents**: List of specialized sub-agents with format:
  ```python
  {
      "name": "agent-name",
      "description": "When to use this agent",
      "prompt": "System prompt for sub-agent",
      "tools": ["optional", "tool", "restrictions"]
  }
  ```

### Example Usage Pattern

See `examples/research/research_agent.py` for comprehensive example with:
- Research sub-agent for deep investigation
- Critique sub-agent for report review
- Iterative research and refinement workflow
- Complex report generation with citations

The framework is designed to replicate Claude Code's deep task execution capabilities in a general-purpose, extensible way.