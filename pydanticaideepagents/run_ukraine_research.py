#!/usr/bin/env python3
"""Run research agent to find latest information about Russia-Ukraine war."""

import os
import sys

# Load environment variables
try:
    from dotenv import load_dotenv
    parent_dir = os.path.dirname(os.path.dirname(__file__))
    env_path = os.path.join(parent_dir, '.env')
    load_dotenv(env_path)
except ImportError:
    print("⚠️  python-dotenv not available")

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pydantic_ai import RunContext
from tavily import TavilyClient
from pydanticaideepagents import create_deep_agent, DeepAgentDependencies
from typing import Literal

# Initialize Tavily client
tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def internet_search(
    ctx: RunContext[DeepAgentDependencies],
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "news",
    include_raw_content: bool = False,
) -> str:
    """Run a web search using Tavily."""
    try:
        results = tavily_client.search(
            query,
            max_results=max_results,
            include_raw_content=include_raw_content,
            topic=topic,
        )
        
        formatted_results = f"Search results for '{query}':\n\n"
        
        for i, result in enumerate(results.get('results', []), 1):
            formatted_results += f"{i}. **{result.get('title', 'No title')}**\n"
            formatted_results += f"   URL: {result.get('url', 'No URL')}\n"
            formatted_results += f"   Content: {result.get('content', 'No content')[:500]}...\n\n"
        
        return formatted_results
        
    except Exception as e:
        return f"Error performing search: {str(e)}"

def main():
    """Run research on Russia-Ukraine conflict."""
    print("🔬 Research Agent: Russia-Ukraine Conflict Latest Developments")
    print("=" * 65)
    
    # Create the research agent
    agent = create_deep_agent(
        tools=[internet_search],
        instructions="""You are an expert news researcher. Your job is to find factual, current information and provide objective reporting.

Use the internet_search tool to find the latest developments. Focus on:
1. Recent military developments
2. Diplomatic efforts and negotiations
3. Humanitarian situation
4. International response and sanctions
5. Economic impacts

Be objective and factual. Cite your sources clearly."""
    )
    
    research_query = """Research the latest developments in the Russia-Ukraine conflict. 
    Provide a comprehensive update covering military, diplomatic, humanitarian, and economic aspects. 
    Focus on developments from 2024 and recent months. Be objective and cite sources."""
    
    print(f"\n📝 Research Query: {research_query}")
    print("-" * 50)
    
    try:
        result = agent.run_sync(research_query)
        
        print("\n🤖 Research Results:")
        print("-" * 20)
        print(result.output)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nPlease ensure you have:")
        print("1. Set TAVILY_API_KEY environment variable")
        print("2. Set ANTHROPIC_API_KEY environment variable")

if __name__ == "__main__":
    main()