#!/usr/bin/env python3
"""
Pydantic AI Deep Agents Runner

This script provides easy commands to test the Pydantic AI Deep Agents implementation
with proper environment loading from the parent directory.
"""

import os
import sys
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description="Run Pydantic AI Deep Agents tests")
    parser.add_argument(
        "test_type", 
        choices=["basic", "simple", "research"],
        default="basic",
        nargs="?",
        help="Type of test to run"
    )
    
    args = parser.parse_args()
    
    # Check if we're in the right directory
    if not os.path.exists("test_basic.py"):
        print("❌ Please run this script from the pydanticaideepagents directory")
        sys.exit(1)
    
    print("🚀 Pydantic AI Deep Agents Runner")
    print("==================================")
    
    # Determine which script to run
    scripts = {
        "basic": ("test_basic.py", "Basic Structure Test (No API keys needed)"),
        "simple": ("examples/research/simple_test.py", "Simple Test with Mock Tools"),
        "research": ("examples/research/research_agent.py", "Full Research Agent Example")
    }
    
    script_path, description = scripts[args.test_type]
    
    print(f"\n📋 Running: {description}")
    print(f"   Script: {script_path}")
    
    # Check if uv is available
    try:
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
        # Use uv run in current environment  
        cmd = ["uv", "run", "python3", script_path]
        print(f"   Command: {' '.join(cmd)}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to regular python
        cmd = ["python3", script_path]
        print(f"   Command: {' '.join(cmd)} (uv not available)")
        print("   ⚠️  Make sure dependencies are installed manually")
    
    print()
    
    # Run the command
    try:
        result = subprocess.run(cmd, cwd=os.getcwd())
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error running command: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()