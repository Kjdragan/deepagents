#!/usr/bin/env python3
"""Debug version of simple test to find where it hangs."""

import sys
import os

# Load environment variables
try:
    from dotenv import load_dotenv
    parent_dir = os.path.dirname(os.path.dirname(__file__))
    env_path = os.path.join(parent_dir, '.env')
    load_dotenv(env_path)
    print(f"✅ Loaded environment from {env_path}")
except ImportError:
    print("⚠️  python-dotenv not available")

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pydantic_ai import RunContext
from pydanticaideepagents import create_deep_agent, DeepAgentDependencies


def mock_search_tool(
    ctx: RunContext[DeepAgentDependencies],
    query: str,
    max_results: int = 3
) -> str:
    """Mock search tool that doesn't require external APIs."""
    print(f"🔍 Mock search called with: {query}")
    
    mock_results = {
        "AI agents": "Recent developments in AI agents include multi-agent systems, autonomous reasoning, and tool integration.",
        "machine learning": "Machine learning advances include large language models, neural architecture search, and federated learning.",
        "python": "Python continues to be popular for AI development with frameworks like PyTorch, TensorFlow, and now Pydantic AI."
    }
    
    # Simple keyword matching
    for keyword, result in mock_results.items():
        if keyword.lower() in query.lower():
            print(f"✅ Mock search returning result for keyword: {keyword}")
            return f"Search results for '{query}':\n\n{result}"
    
    print("✅ Mock search returning general result")
    return f"Search results for '{query}':\n\nGeneral information about the topic."


def test_step_by_step():
    """Test with more debugging."""
    print("🧪 Debug Simple Test")
    print("=" * 25)
    
    print("1. Creating agent...")
    agent = create_deep_agent(
        tools=[mock_search_tool],
        instructions="""You are a helpful research assistant. Use the search tool to find information and provide comprehensive answers.
        
Always use the todo planning tool to organize your work."""
    )
    print("✅ Agent created")
    
    print("2. Starting simple query...")
    try:
        # Use a much simpler query first
        result = agent.run_sync("Hello, just respond with a brief greeting.")
        print(f"✅ Simple query worked: {result.output}")
        
        print("3. Trying query with search tool...")
        result2 = agent.run_sync("Search for 'AI agents' and tell me what you find. Keep it brief.")
        print(f"✅ Search query worked: {result2.output[:100]}...")
        
        print("4. Trying query with planning...")
        result3 = agent.run_sync("Use the todo tool to plan and then search for AI agents. Be concise.")
        print(f"✅ Planning query worked: {result3.output[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = test_step_by_step()
        if success:
            print("🎉 All debug tests passed!")
        else:
            print("❌ Debug tests failed")
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted")
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()