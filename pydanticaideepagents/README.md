# 🧠🤖 Pydantic AI Deep Agents

A Python-centric implementation of Deep Agents using Pydantic AI, preserving all sophisticated prompting and agent coordination capabilities from the LangGraph version while providing better type safety and reduced abstraction.

## Overview

This package implements the same Deep Agent architecture as the original LangGraph DeepAgents but leverages Pydantic AI's dependency injection system and Python-native approach. It maintains identical functionality while providing:

- **Preserved Sophisticated Prompting**: All complex, detailed prompts that enable "deep" agent behavior
- **Shared State Management**: Mock file system and todo management with exact LangGraph semantics  
- **Multi-Agent Coordination**: Sub-agents with shared state and context
- **Dynamic Context Injection**: System prompts that adapt based on current state
- **Type Safety**: Full Pydantic AI type checking and validation
- **Python-Centric**: Reduced abstraction layers for better debugging and customization

## Key Architecture Components

Like the original DeepAgents, this implementation provides four core pillars:

1. **Planning Tool**: Todo management system for task tracking and organization
2. **Sub-Agents**: Specialized agents with shared state for context quarantine  
3. **Mock File System**: Simulated file system enabling agent collaboration and memory
4. **Sophisticated Prompting**: Detailed, context-aware prompts that enable deep agent behavior

## Installation

```bash
pip install pydanticaideepagents
```

For examples with web search:
```bash
pip install pydanticaideepagents[examples]
```

For development:
```bash
pip install pydanticaideepagents[dev]
```

## Quick Start

```python
import os
from typing import Literal
from pydantic_ai import RunContext
from pydanticaideepagents import create_deep_agent, DeepAgentDependencies

# Example tool (same interface as LangGraph version)
def my_search_tool(
    ctx: RunContext[DeepAgentDependencies],
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news"] = "general"
) -> str:
    """Search for information."""
    # Your search implementation here
    return f"Search results for: {query}"

# Create agent (drop-in replacement for LangGraph create_deep_agent)
agent = create_deep_agent(
    tools=[my_search_tool],
    instructions="""You are an expert researcher. Your job is to conduct thorough research, and then write a polished report.

Use the planning tools to organize your work systematically."""
)

# Run the agent (identical API to LangGraph)
result = agent.run_sync("Research the latest developments in AI agents")
print(result.output)
```

## Advanced Usage

### Sub-Agents

Create specialized sub-agents with their own prompts and tools:

```python
subagents = [
    {
        "name": "research-specialist", 
        "description": "Specialized agent for in-depth research tasks",
        "prompt": "You are a research specialist focused on gathering comprehensive information...",
        "tools": ["my_search_tool"]  # Optional: limit tools for this sub-agent
    }
]

agent = create_deep_agent(
    tools=[my_search_tool],
    instructions="You are a research coordinator...",
    subagents=subagents
)
```

### File System Integration

Access the shared file system that enables agent collaboration:

```python
# Initialize with files
initial_files = {
    "research_plan.md": "# Research Plan\n\n1. Topic analysis\n2. Data gathering",
    "sources.txt": "https://example.com/source1\nhttps://example.com/source2"
}

result = agent.run_sync(
    "Continue the research based on the existing plan", 
    initial_files=initial_files
)

# Access files after completion
deps = DeepAgentDependencies()
deps.initialize_with_files(initial_files)
final_result = agent.run_sync("Complete the research", deps=deps)
state = agent.get_state_snapshot(deps)
print("Created files:", list(state['files'].keys()))
```

### Async Usage

```python
async def main():
    result = await agent.run_async("Research quantum computing applications")
    print(result.output)

import asyncio
asyncio.run(main())
```

## Architecture Differences from LangGraph

While maintaining identical functionality, this implementation differs in key ways:

### State Management
- **LangGraph**: Graph-based state updates with reducers
- **Pydantic AI**: Dependency injection with shared object references

### Agent Coordination  
- **LangGraph**: Node-based workflow with message passing
- **Pydantic AI**: Direct method calls with shared dependencies

### Context Injection
- **LangGraph**: Static system prompts with state interpolation
- **Pydantic AI**: Dynamic system prompt functions with RunContext

### Type Safety
- **LangGraph**: Runtime validation with TypedDict
- **Pydantic AI**: Compile-time type checking with Pydantic models

## Examples

### Research Agent

See `examples/research/research_agent.py` for a complete research agent that demonstrates:
- Web search integration with Tavily
- Todo-based planning and progress tracking
- File-based research organization
- Multi-step research workflows

### Running Examples

```bash
# Set required environment variables
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export TAVILY_API_KEY="your-tavily-api-key"

# Run the research example
cd examples/research
python research_agent.py
```

## Compatibility with LangGraph DeepAgents

This implementation provides a drop-in replacement for LangGraph DeepAgents:

```python
# LangGraph version
from deepagents import create_deep_agent

# Pydantic AI version  
from pydanticaideepagents import create_deep_agent

# Same API, same functionality, different architecture
agent = create_deep_agent(tools, instructions)
```

### Migration from LangGraph

1. **Tools**: Add `ctx: RunContext[DeepAgentDependencies]` as first parameter
2. **State Access**: Use `ctx.deps` instead of injected state parameters
3. **File Operations**: Use `ctx.deps.get_file_system()` methods
4. **Todo Management**: Use `ctx.deps.get_todo_manager()` methods

## Model Configuration

By default, uses `claude-sonnet-4-20250514`. Customize with any Pydantic AI model:

```python
from pydantic_ai.models import AnthropicModel

custom_model = AnthropicModel('claude-3-haiku-20240307')
agent = create_deep_agent(
    tools=tools,
    instructions=instructions,
    model=custom_model
)
```

## Development

```bash
git clone https://github.com/deepagents/pydanticaideepagents
cd pydanticaideepagents
pip install -e .[dev]

# Run tests
pytest

# Format code
black src/ examples/
ruff check src/ examples/

# Type checking
mypy src/
```

## Roadmap

- [ ] Phoenix/Arize tracing integration (port from LangGraph version)
- [ ] Human-in-the-loop support
- [ ] Streaming responses
- [ ] Enhanced file system with directories
- [ ] Custom model providers beyond Anthropic
- [ ] Performance benchmarks vs LangGraph version

## License

MIT

## Acknowledgments

This project preserves and adapts the sophisticated prompting and architecture concepts from the original DeepAgents LangGraph implementation, which was inspired by Claude Code and similar deep agent systems.