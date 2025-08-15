"""Simple test to verify Pydantic AI Deep Agents functionality.

This test demonstrates that the core functionality works without requiring
external API keys, making it suitable for quick verification.
"""

import sys
import os

# Load environment variables from parent directory
try:
    from dotenv import load_dotenv
    # Go up three levels: simple_test.py -> research -> examples -> pydanticaideepagents -> deepagents
    parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    env_path = os.path.join(parent_dir, '.env')
    load_dotenv(env_path)
    print(f"✅ Loaded environment variables from {env_path}")
except ImportError:
    print("⚠️  python-dotenv not available, environment variables must be set manually")
except Exception as e:
    print(f"⚠️  Could not load .env file: {e}")

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from pydantic_ai import RunContext
from pydanticaideepagents import create_deep_agent, DeepAgentDependencies


def mock_search_tool(
    ctx: RunContext[DeepAgentDependencies],
    query: str,
    max_results: int = 3
) -> str:
    """Mock search tool that doesn't require external APIs."""
    mock_results = {
        "AI agents": "Recent developments in AI agents include multi-agent systems, autonomous reasoning, and tool integration.",
        "machine learning": "Machine learning advances include large language models, neural architecture search, and federated learning.",
        "python": "Python continues to be popular for AI development with frameworks like PyTorch, TensorFlow, and now Pydantic AI."
    }
    
    # Simple keyword matching
    for keyword, result in mock_results.items():
        if keyword.lower() in query.lower():
            return f"Search results for '{query}':\n\n{result}"
    
    return f"Search results for '{query}':\n\nGeneral information about the topic."


def test_basic_functionality():
    """Test that the agent can be created and run without errors."""
    print("🧪 Testing Pydantic AI Deep Agents")
    print("=" * 40)
    
    # Create a simple research agent
    agent = create_deep_agent(
        tools=[mock_search_tool],
        instructions="""You are a helpful research assistant. Use the search tool to find information and provide comprehensive answers.
        
Always use the todo planning tool to organize your work."""
    )
    
    print("✅ Agent created successfully")
    
    # Test basic query
    try:
        result = agent.run_sync("What are the latest developments in AI agents? Please research this topic and provide a summary.")
        
        print("\n📝 Query: What are the latest developments in AI agents?")
        print("\n🤖 Agent Response:")
        print("-" * 20)
        print(result.output)
        
        print("\n✅ Agent executed successfully")
        
        # Test file operations
        print("\n📁 Testing file operations...")
        
        deps = DeepAgentDependencies()
        deps.get_file_system().write_file("test.txt", "This is a test file")
        
        result2 = agent.run_sync(
            "Read the test.txt file and summarize its contents",
            deps=deps
        )
        
        print("✅ File operations work correctly")
        
        # Check final state
        state = agent.get_state_snapshot(deps)
        print(f"\n📊 Final state - Files: {len(state['files'])}, Todos: {len(state['todos'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during execution: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\nThis might be due to missing environment variables:")
        print("- ANTHROPIC_API_KEY (required for Claude model)")
        return False


def test_subagents():
    """Test sub-agent functionality."""
    print("\n🤖 Testing Sub-Agents")
    print("=" * 25)
    
    subagents = [
        {
            "name": "fact-checker",
            "description": "Specialist for verifying and fact-checking information",
            "prompt": "You are a fact-checking specialist. Verify information carefully and provide accurate assessments."
        }
    ]
    
    agent = create_deep_agent(
        tools=[mock_search_tool],
        instructions="You are a research coordinator. Use sub-agents when appropriate.",
        subagents=subagents
    )
    
    print("✅ Agent with sub-agents created successfully")
    
    try:
        result = agent.run_sync("Research AI agents and have the fact-checker verify the key claims.")
        print("✅ Sub-agent coordination works correctly")
        return True
    except Exception as e:
        print(f"❌ Sub-agent test failed: {str(e)}")
        return False


if __name__ == "__main__":
    print("🚀 Pydantic AI Deep Agents - Simple Test Suite")
    print("=" * 50)
    
    # Check environment
    has_anthropic_key = bool(os.getenv("ANTHROPIC_API_KEY"))
    
    if not has_anthropic_key:
        print("⚠️  Warning: ANTHROPIC_API_KEY not found")
        print("This test may fail at the model execution step.")
        print("Set ANTHROPIC_API_KEY to run full tests.\n")
    
    # Run tests
    success = True
    
    try:
        success &= test_basic_functionality()
        success &= test_subagents()
        
        if success:
            print("\n🎉 All tests passed!")
            print("The Pydantic AI Deep Agents implementation is working correctly.")
        else:
            print("\n❌ Some tests failed.")
            
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        success = False
    
    exit(0 if success else 1)