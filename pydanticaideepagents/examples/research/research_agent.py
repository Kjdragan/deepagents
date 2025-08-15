"""Research agent example using Pydantic AI Deep Agents.

This example demonstrates the same functionality as the LangGraph research agent
but implemented using Pydantic AI Deep Agents with preserved sophisticated prompting.
"""

import os
import asyncio
from typing import Literal
from pydantic_ai import RunContext

# Import the Tavily client for web search
try:
    from tavily import TavilyClient
except ImportError:
    print("Please install tavily-python: pip install tavily-python")
    exit(1)

# Import our Pydantic AI Deep Agents
from pydanticaideepagents import create_deep_agent, DeepAgentDependencies


# Initialize Tavily client
tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


def internet_search(
    ctx: RunContext[DeepAgentDependencies],
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
) -> str:
    """Run a web search using Tavily.
    
    Args:
        ctx: Pydantic AI run context with dependencies
        query: Search query
        max_results: Maximum number of results to return
        topic: Topic category for the search
        include_raw_content: Whether to include raw content
        
    Returns:
        Search results as a formatted string
    """
    try:
        results = tavily_client.search(
            query,
            max_results=max_results,
            include_raw_content=include_raw_content,
            topic=topic,
        )
        
        # Format results for the agent
        formatted_results = f"Search results for '{query}':\n\n"
        
        for i, result in enumerate(results.get('results', []), 1):
            formatted_results += f"{i}. **{result.get('title', 'No title')}**\n"
            formatted_results += f"   URL: {result.get('url', 'No URL')}\n"
            formatted_results += f"   Content: {result.get('content', 'No content')[:500]}...\n\n"
        
        return formatted_results
        
    except Exception as e:
        return f"Error performing search: {str(e)}"


# Research instructions (identical to LangGraph version)
research_instructions = """You are an expert researcher. Your job is to conduct thorough research, and then write a polished report.

You have access to a few tools.

## `internet_search`

Use this to run an internet search for a given query. You can specify the number of results, the topic, and whether raw content should be included.

## Planning and Organization

Use the `write_todos` tool to plan your research systematically:
1. Break down the research topic into specific questions
2. Plan your search strategy  
3. Track your progress as you gather information
4. Plan the structure of your final report

## File Management

Use the file system tools to organize your research:
- Create files to store research notes for different aspects of your topic
- Use files to draft sections of your report
- Keep track of sources and citations

Remember to be thorough, accurate, and well-organized in your research approach."""


def create_research_agent():
    """Create a research agent with the same functionality as the LangGraph version."""
    return create_deep_agent(
        tools=[internet_search],
        instructions=research_instructions,
    )


async def main():
    """Demonstrate the research agent functionality."""
    print("🔬 Pydantic AI Deep Agents Research Demo")
    print("=" * 50)
    
    # Create the research agent
    agent = create_research_agent()
    
    # Example research query
    research_query = "What are the latest developments in large language models in 2024?"
    
    print(f"\n📝 Research Query: {research_query}")
    print("-" * 50)
    
    try:
        # Run the agent asynchronously
        result = await agent.run_async(research_query)
        
        print("\n🤖 Agent Response:")
        print("-" * 20)
        print(result.output)
        
        # Show the state after completion
        print("\n📊 Final State:")
        print("-" * 15)
        
        # Access the dependencies to show the state
        # Note: In a real implementation, you'd get this from the run result
        deps = DeepAgentDependencies()
        state = agent.get_state_snapshot(deps)
        
        print(f"Files created: {list(state['files'].keys())}")
        print(f"Todos completed: {len([t for t in state['todos'] if t['status'] == 'completed'])}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nPlease ensure you have:")
        print("1. Set TAVILY_API_KEY environment variable")
        print("2. Set ANTHROPIC_API_KEY environment variable")
        print("3. Installed required dependencies")


def run_sync_example():
    """Demonstrate synchronous usage (similar to LangGraph example)."""
    print("🔬 Pydantic AI Deep Agents Research Demo (Sync)")
    print("=" * 55)
    
    # Create the research agent
    agent = create_research_agent()
    
    # Example research query
    research_query = "What is LangGraph and how does it work?"
    
    print(f"\n📝 Research Query: {research_query}")
    print("-" * 50)
    
    try:
        # Run the agent synchronously (matches LangGraph API)
        result = agent.run_sync(research_query)
        
        print("\n🤖 Agent Response:")
        print("-" * 20)
        print(result.output)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    print("Choose execution mode:")
    print("1. Async example (recommended)")
    print("2. Sync example (LangGraph-style)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        asyncio.run(main())
    elif choice == "2":
        run_sync_example()
    else:
        print("Invalid choice. Running async example...")
        asyncio.run(main())