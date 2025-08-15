#!/bin/bash

echo "🚀 Pydantic AI Deep Agents Runner"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "test_basic.py" ]; then
    echo "❌ Please run this script from the pydanticaideepagents directory"
    exit 1
fi

# Function to run with uv if available, fallback to python
run_with_uv() {
    local script=$1
    local description=$2
    
    echo ""
    echo "📋 Running: $description"
    echo "   Script: $script"
    echo "   Command: uv run --project=.. python3 $script"
    echo ""
    
    # Use uv run with parent project context to get dependencies
    uv run --project=.. python3 $script
}

# Parse command line argument
case "${1:-basic}" in
    "basic")
        run_with_uv "test_basic.py" "Basic Structure Test (No API keys needed)"
        ;;
    "simple")
        run_with_uv "examples/research/simple_test.py" "Simple Test with Mock Tools"
        ;;
    "research")
        run_with_uv "examples/research/research_agent.py" "Full Research Agent Example"
        ;;
    *)
        echo "Usage: $0 [basic|simple|research]"
        echo ""
        echo "Commands:"
        echo "  basic    - Test core structure without API calls"
        echo "  simple   - Test with mock tools (requires pydantic-ai)"
        echo "  research - Full research example (requires pydantic-ai + API keys)"
        echo ""
        echo "Examples:"
        echo "  $0 basic      # Test without dependencies"
        echo "  $0 simple     # Test with pydantic-ai"
        echo "  $0 research   # Full demo with web search"
        exit 1
        ;;
esac