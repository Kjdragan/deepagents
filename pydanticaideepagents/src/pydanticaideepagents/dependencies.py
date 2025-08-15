"""Dependency injection system for Pydantic AI Deep Agents.

This module provides the shared state management through Pydantic AI's
RunContext dependency injection system, enabling multi-agent coordination.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from .mock_filesystem import MockFileSystem
from .todo_manager import TodoManager, Todo


@dataclass
class DeepAgentDependencies:
    """Shared dependencies for all agents in the Deep Agent system.
    
    This class serves as the central state container that gets injected
    into all agents and tools through Pydantic AI's RunContext system.
    It provides the same functionality as LangGraph's shared state.
    """
    filesystem: MockFileSystem = field(default_factory=MockFileSystem)
    todo_manager: TodoManager = field(default_factory=TodoManager)
    agent_metadata: Dict[str, Any] = field(default_factory=dict)
    run_context: Dict[str, Any] = field(default_factory=dict)
    
    def get_file_system(self) -> MockFileSystem:
        """Get the shared mock file system."""
        return self.filesystem
    
    def get_todo_manager(self) -> TodoManager:
        """Get the shared todo manager."""
        return self.todo_manager
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata for the agent run."""
        self.agent_metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata for the agent run."""
        return self.agent_metadata.get(key, default)
    
    def set_context(self, key: str, value: Any) -> None:
        """Set context information for the run."""
        self.run_context[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get context information for the run."""
        return self.run_context.get(key, default)
    
    def initialize_with_files(self, files: Optional[Dict[str, str]] = None) -> None:
        """Initialize the filesystem with initial files.
        
        Args:
            files: Optional dictionary of filename -> content mappings
        """
        if files:
            self.filesystem.update_files(files)
    
    def get_state_snapshot(self) -> Dict[str, Any]:
        """Get a snapshot of the current state for debugging/inspection.
        
        Returns:
            Dictionary containing current state information
        """
        return {
            "files": self.filesystem.get_files_dict(),
            "todos": [{"content": todo.content, "status": todo.status, "id": todo.id} for todo in self.todo_manager.get_todos()],
            "metadata": self.agent_metadata.copy(),
            "context": self.run_context.copy()
        }