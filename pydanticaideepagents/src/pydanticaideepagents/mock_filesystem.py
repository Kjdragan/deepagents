"""Mock filesystem implementation for Pydantic AI Deep Agents.

This module provides a simulated file system that enables agent collaboration
and memory persistence exactly as in the LangGraph DeepAgents system.
All file operations are performed in-memory with identical semantics.
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class MockFileSystem:
    """Mock file system that replicates LangGraph DeepAgents functionality.
    
    This provides in-memory file storage with identical behavior to the
    LangGraph version, enabling seamless migration of existing prompts
    and agent workflows.
    """
    files: Dict[str, str] = field(default_factory=dict)
    
    def ls(self) -> list[str]:
        """List all files in the mock filesystem."""
        return list(self.files.keys())
    
    def read_file(
        self, 
        file_path: str, 
        offset: int = 0, 
        limit: int = 2000
    ) -> str:
        """Read file with exact LangGraph semantics.
        
        Args:
            file_path: Path to the file
            offset: Line number to start reading from (0-based)
            limit: Maximum number of lines to read
            
        Returns:
            File content formatted with line numbers (cat -n format)
        """
        if file_path not in self.files:
            return f"Error: File '{file_path}' not found"
        
        content = self.files[file_path]
        
        # Handle empty file
        if not content or content.strip() == "":
            return "System reminder: File exists but has empty contents"
        
        # Split content into lines
        lines = content.splitlines()
        
        # Apply line offset and limit
        start_idx = offset
        end_idx = min(start_idx + limit, len(lines))
        
        # Handle case where offset is beyond file length
        if start_idx >= len(lines):
            return f"Error: Line offset {offset} exceeds file length ({len(lines)} lines)"
        
        # Format output with line numbers (cat -n format)
        result_lines = []
        for i in range(start_idx, end_idx):
            line_content = lines[i]
            
            # Truncate lines longer than 2000 characters
            if len(line_content) > 2000:
                line_content = line_content[:2000]
            
            # Line numbers start at 1, so add 1 to the index
            line_number = i + 1
            result_lines.append(f"{line_number:6d}\t{line_content}")
        
        return "\n".join(result_lines)
    
    def write_file(self, file_path: str, content: str) -> str:
        """Write content to a file.
        
        Args:
            file_path: Path to the file
            content: Content to write
            
        Returns:
            Success message
        """
        self.files[file_path] = content
        return f"Updated file {file_path}"
    
    def edit_file(
        self, 
        file_path: str, 
        old_string: str, 
        new_string: str, 
        replace_all: bool = False
    ) -> str:
        """Edit file with exact LangGraph semantics.
        
        Args:
            file_path: Path to the file
            old_string: String to replace
            new_string: Replacement string
            replace_all: Whether to replace all occurrences
            
        Returns:
            Success message or error description
        """
        if file_path not in self.files:
            return f"Error: File '{file_path}' not found"
        
        content = self.files[file_path]
        
        # Check if old_string exists in the file
        if old_string not in content:
            return f"Error: String not found in file: '{old_string}'"
        
        # If not replace_all, check for uniqueness
        if not replace_all:
            occurrences = content.count(old_string)
            if occurrences > 1:
                return f"Error: String '{old_string}' appears {occurrences} times in file. Use replace_all=True to replace all instances, or provide a more specific string with surrounding context."
            elif occurrences == 0:
                return f"Error: String not found in file: '{old_string}'"
        
        # Perform the replacement
        if replace_all:
            new_content = content.replace(old_string, new_string)
            replacement_count = content.count(old_string)
            self.files[file_path] = new_content
            return f"Successfully replaced {replacement_count} instance(s) of the string in '{file_path}'"
        else:
            new_content = content.replace(old_string, new_string, 1)
            self.files[file_path] = new_content
            return f"Successfully replaced string in '{file_path}'"
    
    def get_files_dict(self) -> Dict[str, str]:
        """Get the current files dictionary for state management."""
        return self.files.copy()
    
    def update_files(self, files_dict: Dict[str, str]) -> None:
        """Update the files from a dictionary (for state synchronization)."""
        self.files.update(files_dict)
    
    def clear(self) -> None:
        """Clear all files from the filesystem."""
        self.files.clear()