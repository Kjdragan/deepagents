# Phoenix Observation Platform (Arize AI) Tracing Implementation Guide for DeepAgents

## Table of Contents
1. [Overview](#overview)
2. [Installation & Setup](#installation--setup)
3. [Core Implementation](#core-implementation)
4. [LangGraph Integration](#langgraph-integration)
5. [Agent Metadata & Hierarchy](#agent-metadata--hierarchy)
6. [CLI Integration](#cli-integration)
7. [Configuration Guide](#configuration-guide)
8. [Usage Examples](#usage-examples)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

## Overview

Phoenix Observation Platform (Arize AI) provides comprehensive observability for AI agent systems. This implementation guide covers LangGraph-only tracing for the DeepAgents project, leveraging automatic LangChain instrumentation to capture all agent workflows and model interactions.

### Key Benefits for DeepAgents
- **Complete Agent Workflow Tracing**: Automatic capture of all LangGraph agent executions
- **Model Call Tracking**: All Anthropic model calls traced through LangChain instrumentation
- **Sub-Agent Hierarchy**: Proper parent-child relationship tracking for multi-agent systems
- **Token Usage Monitoring**: Automatic token consumption tracking through underlying models
- **Minimal Implementation**: Single instrumentation covers all agent and model interactions

## Installation & Setup

### Dependencies

The following packages have been added to `pyproject.toml`:

```toml
dependencies = [
    # Existing dependencies...
    "openinference-instrumentation-langchain>=0.1.27",
    "arize-otel>=0.13.0",
    "opentelemetry-sdk>=1.26.0",
    "opentelemetry-exporter-otlp>=1.26.0",
]
```

### Environment Variables

Configure these variables in your `.env` file:

```bash
# Required for all operations
ANTHROPIC_API_KEY=your_anthropic_api_key

# Required for research functionality  
TAVILY_API_KEY=your_tavily_api_key

# Required for Phoenix/Arize tracing
ARIZE_API_KEY=your_arize_api_key
ARIZE_SPACE_ID=your_space_id_here  # Replace with your actual Space ID
```

**Finding your Space ID:**
1. Log into [Arize platform](https://app.arize.com)
2. Navigate to your space
3. Copy the Space ID from the URL or settings

## Core Implementation

### Tracing Module (`src/deepagents/tracing.py`)

The core tracing functionality is implemented in a dedicated module:

```python
from deepagents.tracing import initialize_tracing, is_tracing_enabled, get_trace_url

# Initialize tracing (automatically done in create_deep_agent)
initialize_tracing(project_name="my-project")

# Check status
if is_tracing_enabled():
    print(f"View traces at: {get_trace_url()}")
```

### Key Functions

- `initialize_tracing()`: Sets up Arize OTEL and LangChain instrumentation
- `is_tracing_enabled()`: Check if tracing is active
- `get_trace_url()`: Get Arize platform URL for viewing traces
- `configure_agent_metadata()`: Set up agent hierarchy tracking
- `log_agent_invocation()`: Log agent creation and execution

## LangGraph Integration

### Automatic Agent Tracing

The `create_deep_agent()` function now includes automatic tracing:

```python
from deepagents import create_deep_agent

# Tracing enabled by default
agent = create_deep_agent(
    tools=[your_tools],
    instructions="Your agent instructions",
    enable_tracing=True,  # Default: True
    project_name="my-project"  # Default: "deepagents"
)
```

### What Gets Traced

With LangGraph instrumentation, the following are automatically captured:

- **Agent Invocations**: All calls to LangGraph agents
- **Tool Usage**: Every tool call and response
- **Model Interactions**: All Anthropic model calls through LangChain
- **Token Consumption**: Token usage for each model call
- **Workflow Steps**: Complete agent execution flow
- **Sub-Agent Spawning**: Parent-child agent relationships

## Agent Metadata & Hierarchy

### Parent-Child Relationships

Sub-agents are automatically tracked with proper hierarchy:

```python
# Main agent creation
main_agent = create_deep_agent(
    tools=tools,
    instructions="Main agent instructions",
    agent_id="main-agent-001"  # Optional: auto-generated if not provided
)

# Sub-agents inherit parent tracking automatically
# When main agent spawns sub-agents via the task tool, 
# hierarchy is preserved in traces
```

### Agent Metadata

Each agent automatically receives metadata for tracing:

- `graph.node.id`: Unique agent identifier
- `graph.node.parent_id`: Parent agent for sub-agents
- Thread tracking for conversation flows

## CLI Integration

### Research Command with Tracing

```bash
# Run research with tracing (enabled by default)
deepagents research "What is LangGraph?" 

# Disable tracing
deepagents research "What is LangGraph?" --no-enable-tracing

# Custom model with tracing
deepagents research "AI trends" --model opus --enable-tracing
```

### Tracing Status Command

```bash
# Check tracing configuration
deepagents tracing-status
```

Output includes:
- Environment variable validation
- Tracing initialization test
- Arize platform URL
- Configuration troubleshooting

## Configuration Guide

### Environment Setup

1. **Install Dependencies**:
   ```bash
   uv sync  # or pip install -e .
   ```

2. **Configure Environment Variables**:
   ```bash
   export ARIZE_API_KEY="your_api_key"
   export ARIZE_SPACE_ID="your_space_id" 
   ```

3. **Test Configuration**:
   ```bash
   deepagents tracing-status
   ```

### Project Configuration

```python
# Custom project setup
agent = create_deep_agent(
    tools=my_tools,
    instructions="Custom instructions",
    enable_tracing=True,
    project_name="my-custom-project",  # Will appear in Arize
    agent_id="custom-agent-001"       # Optional custom ID
)
```

## Usage Examples

### Basic Agent with Tracing

```python
from deepagents import create_deep_agent
from deepagents.tracing import get_trace_url

def my_tool(query: str) -> str:
    """Example tool function."""
    return f"Processed: {query}"

# Create agent with automatic tracing
agent = create_deep_agent(
    tools=[my_tool],
    instructions="You are a helpful assistant.",
    project_name="example-project"
)

# Run agent
result = agent.invoke({"messages": [{"role": "user", "content": "Hello"}]})

# View traces
print(f"View traces at: {get_trace_url()}")
```

### Multi-Agent System Tracing

```python
# Main research agent with sub-agents
research_subagent = {
    "name": "research-agent",
    "description": "Conducts detailed research",
    "prompt": "You are a research specialist...",
}

agent = create_deep_agent(
    tools=[internet_search],
    instructions="You are a research coordinator.",
    subagents=[research_subagent],
    project_name="multi-agent-research"
)

# All agent interactions (main + sub) are traced with hierarchy
result = agent.invoke({"messages": [{"role": "user", "content": "Research AI trends"}]})
```

## Best Practices

### 1. Project Organization
- Use descriptive project names for different agent types
- Group related agents under the same project
- Use consistent naming conventions for agent IDs

### 2. Performance Optimization
- Tracing adds minimal overhead (~1-5ms per operation)
- No performance tuning required for typical usage
- Large-scale deployments: monitor trace volume

### 3. Security
- Never log sensitive data in agent metadata
- Use environment variables for API keys
- Restrict Arize access to authorized personnel

### 4. Monitoring
- Use `tracing-status` command for health checks
- Monitor trace URL accessibility
- Set up alerts for tracing failures

## Troubleshooting

### Common Issues

#### 1. Tracing Not Initializing
**Symptoms**: No traces appearing in Arize
```bash
# Check configuration
deepagents tracing-status

# Common fixes:
export ARIZE_SPACE_ID="correct_space_id"  # Not "your_space_id_here"
export ARIZE_API_KEY="valid_api_key"
```

#### 2. Missing Agent Hierarchy
**Symptoms**: Sub-agents not showing parent relationships
- Ensure `enable_tracing=True` in `create_deep_agent()`
- Verify sub-agents are created through the task tool
- Check that parent agent has proper agent_id

#### 3. Import Errors
**Symptoms**: Module import failures
```bash
# Install missing dependencies
uv sync
# or
pip install openinference-instrumentation-langchain arize-otel
```

#### 4. Environment Variable Issues
**Symptoms**: Configuration warnings
```bash
# Verify environment variables are loaded
python -c "import os; print(os.getenv('ARIZE_SPACE_ID'))"

# Check .env file location and format
cat .env
```

### Debug Logging

Enable debug logging for detailed tracing information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Tracing module will output detailed debug information
from deepagents.tracing import initialize_tracing
initialize_tracing(project_name="debug-test")
```

### Support Resources

- **Arize Documentation**: https://arize.com/docs/ax
- **Platform Access**: https://app.arize.com
- **LangGraph Integration**: https://arize.com/docs/ax/integrations/frameworks-and-platforms/langgraph
- **OpenInference**: https://github.com/Arize-ai/openinference

---

This implementation provides comprehensive observability for DeepAgents through a single LangGraph instrumentation that automatically captures all agent workflows, tool usage, and model interactions including token consumption tracking.