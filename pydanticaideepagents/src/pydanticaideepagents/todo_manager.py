"""Todo management system for Pydantic AI Deep Agents.

This module provides todo list functionality that exactly replicates
the LangGraph DeepAgents todo system with identical semantics.
"""

from typing import List, Literal, Optional
from dataclasses import dataclass, field


@dataclass
class Todo:
    """Todo item with exact LangGraph schema."""
    content: str
    status: Literal["pending", "in_progress", "completed"]
    id: str


@dataclass
class TodoManager:
    """Manages todo lists with exact LangGraph DeepAgents functionality."""
    todos: List[Todo] = field(default_factory=list)
    
    def write_todos(self, todos: List[Todo]) -> str:
        """Update the todo list with exact LangGraph semantics.
        
        Args:
            todos: List of Todo items to set
            
        Returns:
            Success message
        """
        self.todos = todos
        return f"Updated todo list to {todos}"
    
    def get_todos(self) -> List[Todo]:
        """Get current todo list."""
        return self.todos.copy()
    
    def add_todo(self, content: str, todo_id: str, status: Literal["pending", "in_progress", "completed"] = "pending") -> str:
        """Add a new todo item.
        
        Args:
            content: Description of the todo
            todo_id: Unique identifier for the todo
            status: Initial status
            
        Returns:
            Success message
        """
        todo = Todo(content=content, status=status, id=todo_id)
        self.todos.append(todo)
        return f"Added todo: {content}"
    
    def update_todo_status(self, todo_id: str, status: Literal["pending", "in_progress", "completed"]) -> str:
        """Update a todo's status.
        
        Args:
            todo_id: ID of the todo to update
            status: New status
            
        Returns:
            Success message or error
        """
        for todo in self.todos:
            if todo.id == todo_id:
                todo.status = status
                return f"Updated todo {todo_id} status to {status}"
        return f"Error: Todo with ID {todo_id} not found"
    
    def clear_todos(self) -> str:
        """Clear all todos."""
        self.todos = []
        return "Cleared all todos"