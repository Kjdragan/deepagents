#!/usr/bin/env python3
"""Test environment variable loading."""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("🔍 Environment Variable Test")
print("=" * 30)

print(f"Current file: {__file__}")
print(f"Current dir: {os.path.dirname(__file__)}")

# Try to load environment variables like simple_test.py does
try:
    from dotenv import load_dotenv
    # Go up three levels: test_env.py -> pydanticaideepagents -> deepagents
    parent_dir = os.path.dirname(os.path.dirname(__file__))
    env_path = os.path.join(parent_dir, '.env')
    print(f"Looking for .env at: {env_path}")
    print(f"Exists: {os.path.exists(env_path)}")
    
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from {env_path}")
    else:
        print(f"❌ .env file not found at {env_path}")
        
except ImportError:
    print("⚠️  python-dotenv not available")
except Exception as e:
    print(f"⚠️  Could not load .env file: {e}")

# Check if API key is available
api_key = os.getenv("ANTHROPIC_API_KEY")
if api_key:
    print(f"✅ ANTHROPIC_API_KEY found: {api_key[:10]}...")
else:
    print("❌ ANTHROPIC_API_KEY not found")

print(f"All env vars: {list(os.environ.keys())}")