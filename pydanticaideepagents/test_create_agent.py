#!/usr/bin/env python3
"""Test the create_deep_agent function specifically."""

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

print("🔍 Testing create_deep_agent function")
print("=" * 40)

try:
    print("1. Importing create_deep_agent...")
    from pydanticaideepagents import create_deep_agent, DeepAgentDependencies
    print("✅ Imported successfully")
    
    print("2. Creating simple mock tool...")
    from pydantic_ai import RunContext
    
    def mock_tool(ctx: RunContext[DeepAgentDependencies], query: str) -> str:
        """Mock tool for testing."""
        return f"Mock result for: {query}"
    
    print("✅ Mock tool created")
    
    print("3. Calling create_deep_agent...")
    agent = create_deep_agent(
        tools=[mock_tool],
        instructions="You are a test agent."
    )
    print("✅ Agent created successfully")
    
    print("4. Creating dependencies...")
    deps = DeepAgentDependencies()
    print("✅ Dependencies created")
    
    print("🎉 All steps completed successfully!")
    
except Exception as e:
    print(f"💥 Error: {e}")
    import traceback
    traceback.print_exc()