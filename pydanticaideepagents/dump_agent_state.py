#!/usr/bin/env python3
"""Dump agent state to see what happened during research."""

import os
import sys
import json

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
    """Run research and dump all internal state."""
    print("🔬 Research Agent with State Dump")
    print("=" * 40)
    
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

IMPORTANT: Use the file system tools to organize your research:
- Create separate files for different aspects (military.md, diplomatic.md, etc.)
- Save your research notes and findings
- Keep track of sources and citations
- Draft your final report in a file called final_report.md

IMPORTANT: Use the write_todos tool to plan your research:
- Break down the research into specific tasks
- Track your progress as you complete each search
- Plan the structure of your report

Be objective and factual. Cite your sources clearly."""
    )
    
    # Create shared dependencies to track state
    deps = DeepAgentDependencies()
    
    research_query = """Research the latest developments in the Russia-Ukraine conflict. 
    Provide a comprehensive update covering military, diplomatic, humanitarian, and economic aspects. 
    Focus on developments from 2024 and recent months. Be objective and cite sources.
    
    Please organize your research systematically using files and todos."""
    
    print(f"\n📝 Research Query: {research_query}")
    print("-" * 50)
    
    try:
        # Run with shared dependencies
        result = agent.run_sync(research_query, deps=deps)
        
        print("\n🤖 Agent Response:")
        print("-" * 20)
        print(result.output)
        
        print("\n" + "="*60)
        print("📊 INTERNAL AGENT STATE DUMP")
        print("="*60)
        
        # Get the file system state
        filesystem = deps.get_file_system()
        files = filesystem.files
        
        print(f"\n📁 Files Created: {len(files)}")
        print("-" * 30)
        
        for filename, content in files.items():
            print(f"\n📄 File: {filename}")
            print("─" * (len(filename) + 8))
            print(content)
            print("\n" + "─" * 50)
        
        # Get the todo state
        todo_manager = deps.get_todo_manager()
        todos = todo_manager.todos
        
        print(f"\n✅ Todos: {len(todos)}")
        print("-" * 20)
        
        for i, todo in enumerate(todos, 1):
            status_icon = "✅" if todo['status'] == 'completed' else "🔄" if todo['status'] == 'in_progress' else "⏳"
            print(f"{i}. {status_icon} [{todo['status']}] {todo['content']}")
        
        print(f"\n📈 Summary:")
        print(f"- Total files: {len(files)}")
        print(f"- Total todos: {len(todos)}")
        print(f"- Completed todos: {len([t for t in todos if t['status'] == 'completed'])}")
        print(f"- In progress todos: {len([t for t in todos if t['status'] == 'in_progress'])}")
        
        # Save state to a file for review
        state_dump = {
            "agent_response": result.output,
            "files": files,
            "todos": todos,
            "summary": {
                "total_files": len(files),
                "total_todos": len(todos),
                "completed_todos": len([t for t in todos if t['status'] == 'completed']),
                "in_progress_todos": len([t for t in todos if t['status'] == 'in_progress'])
            }
        }
        
        with open("agent_state_dump.json", "w") as f:
            json.dump(state_dump, f, indent=2)
        
        print(f"\n💾 State saved to: agent_state_dump.json")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()