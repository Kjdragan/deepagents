#!/usr/bin/env python3
"""Test actually running the agent."""

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

print("🔍 Testing agent execution")
print("=" * 30)

try:
    print("1. Importing...")
    from pydanticaideepagents import create_deep_agent, DeepAgentDependencies
    from pydantic_ai import RunContext
    print("✅ Imported successfully")
    
    print("2. Creating mock tool...")
    def mock_tool(ctx: RunContext[DeepAgentDependencies], query: str) -> str:
        """Mock tool for testing."""
        return f"Mock result for: {query}"
    
    print("3. Creating agent...")
    agent = create_deep_agent(
        tools=[mock_tool],
        instructions="You are a test agent. Just respond briefly."
    )
    print("✅ Agent created")
    
    print("4. Running simple query...")
    result = agent.run_sync("Hello, just say hi back")
    print(f"✅ Agent responded: {result.output}")
    
    print("🎉 Test completed successfully!")
    
except Exception as e:
    print(f"💥 Error: {e}")
    import traceback
    traceback.print_exc()