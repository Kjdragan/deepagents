#!/usr/bin/env python3
"""Minimal test to identify where agent creation hangs."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("🔍 Starting debug test...")

# Load environment variables from parent .env file
try:
    from dotenv import load_dotenv
    parent_env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(parent_env_path)
    print("✅ Environment variables loaded")
except ImportError:
    print("⚠️  python-dotenv not available, using existing environment")

try:
    print("1. Importing dependencies...")
    from pydanticaideepagents.dependencies import DeepAgentDependencies
    print("✅ Dependencies imported")
    
    print("2. Importing Agent...")
    from pydantic_ai import Agent
    print("✅ Agent imported")
    
    print("3. Importing model...")
    from pydantic_ai.models.anthropic import AnthropicModel
    print("✅ Model imported")
    
    print("4. Creating model instance...")
    model = AnthropicModel('claude-3-5-sonnet-20241022')
    print("✅ Model created")
    
    print("5. Creating basic agent...")
    agent = Agent(
        model,
        deps_type=DeepAgentDependencies,
    )
    print("✅ Basic agent created")
    
    print("6. Adding tool with decorator...")
    @agent.tool
    def test_tool(ctx) -> str:
        """Test tool."""
        return "test"
    print("✅ Tool added")
    
    print("7. Adding system prompt...")
    @agent.system_prompt  
    def test_prompt(ctx) -> str:
        return "You are a test agent."
    print("✅ System prompt added")
    
    print("8. Creating dependencies...")
    deps = DeepAgentDependencies()
    print("✅ Dependencies created")
    
    print("🎉 All steps completed successfully!")
    
except Exception as e:
    print(f"💥 Error at step: {e}")
    import traceback
    traceback.print_exc()