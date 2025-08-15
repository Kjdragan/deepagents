"""Basic structure test for Pydantic AI Deep Agents.

This test verifies the core classes can be imported and instantiated
without running any actual agent logic that would require API keys.
"""

import sys
import os

# Load environment variables from parent directory
try:
    from dotenv import load_dotenv
    parent_dir = os.path.dirname(os.path.dirname(__file__))
    env_path = os.path.join(parent_dir, '.env')
    load_dotenv(env_path)
    print(f"✅ Loaded environment variables from {env_path}")
except ImportError:
    print("⚠️  python-dotenv not available, environment variables must be set manually")
except Exception as e:
    print(f"⚠️  Could not load .env file: {e}")

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all modules can be imported."""
    print("🧪 Testing imports...")
    
    try:
        from pydanticaideepagents.mock_filesystem import MockFileSystem
        print("✅ MockFileSystem imported")
        
        from pydanticaideepagents.todo_manager import TodoManager, Todo
        print("✅ TodoManager and Todo imported")
        
        from pydanticaideepagents.dependencies import DeepAgentDependencies  
        print("✅ DeepAgentDependencies imported")
        
        # Skip importing the main DeepAgent for now since it requires pydantic_ai
        # from pydanticaideepagents.deep_agent import DeepAgent
        # print("✅ DeepAgent imported")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_basic_classes():
    """Test basic functionality of core classes."""
    print("\n🧪 Testing basic class functionality...")
    
    try:
        from pydanticaideepagents.mock_filesystem import MockFileSystem
        from pydanticaideepagents.todo_manager import TodoManager, Todo
        from pydanticaideepagents.dependencies import DeepAgentDependencies
        
        # Test MockFileSystem
        fs = MockFileSystem()
        fs.write_file("test.txt", "Hello world")
        content = fs.read_file("test.txt")
        assert "Hello world" in content
        print("✅ MockFileSystem basic operations work")
        
        # Test TodoManager
        todo_mgr = TodoManager()
        test_todo = Todo(content="Test task", status="pending", id="test-1")
        todo_mgr.write_todos([test_todo])
        todos = todo_mgr.get_todos()
        assert len(todos) == 1
        assert todos[0].content == "Test task"
        print("✅ TodoManager basic operations work")
        
        # Test Dependencies
        deps = DeepAgentDependencies()
        deps.get_file_system().write_file("deps_test.txt", "Test content")
        files = deps.get_file_system().ls()
        assert "deps_test.txt" in files
        print("✅ DeepAgentDependencies basic operations work")
        
        return True
        
    except Exception as e:
        print(f"❌ Class test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_system_semantics():
    """Test that file system matches LangGraph semantics exactly."""
    print("\n🧪 Testing file system LangGraph compatibility...")
    
    try:
        from pydanticaideepagents.mock_filesystem import MockFileSystem
        
        fs = MockFileSystem()
        
        # Test empty file behavior
        fs.write_file("empty.txt", "")
        result = fs.read_file("empty.txt")
        assert "System reminder: File exists but has empty contents" in result
        print("✅ Empty file behavior matches LangGraph")
        
        # Test file not found
        result = fs.read_file("nonexistent.txt")
        assert "Error: File 'nonexistent.txt' not found" in result
        print("✅ File not found behavior matches LangGraph")
        
        # Test line numbering
        fs.write_file("multiline.txt", "Line 1\nLine 2\nLine 3")
        result = fs.read_file("multiline.txt")
        assert "     1\tLine 1" in result
        assert "     2\tLine 2" in result
        assert "     3\tLine 3" in result
        print("✅ Line numbering format matches LangGraph")
        
        # Test edit functionality
        fs.write_file("edit_test.txt", "Hello world")
        result = fs.edit_file("edit_test.txt", "world", "Pydantic AI")
        assert "Successfully replaced string" in result
        content = fs.read_file("edit_test.txt") 
        assert "Hello Pydantic AI" in content
        print("✅ Edit functionality matches LangGraph")
        
        return True
        
    except Exception as e:
        print(f"❌ File system test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Pydantic AI Deep Agents - Basic Structure Test")
    print("=" * 55)
    
    success = True
    
    success &= test_imports()
    success &= test_basic_classes() 
    success &= test_file_system_semantics()
    
    if success:
        print("\n🎉 All basic tests passed!")
        print("Core structure is working correctly.")
    else:
        print("\n❌ Some basic tests failed.")
        print("Core structure needs fixes.")
    
    exit(0 if success else 1)