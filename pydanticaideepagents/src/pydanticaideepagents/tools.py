"""Tools for Pydantic AI Deep Agents.

This module provides all the tools (file system operations, planning, etc.)
with exact LangGraph DeepAgents semantics, adapted for Pydantic AI's architecture.
"""

from typing import List, Optional
from pydantic_ai import RunContext
from .dependencies import DeepAgentDependencies
from .todo_manager import Todo


def ls_tool(ctx: RunContext[DeepAgentDependencies]) -> List[str]:
    """List all files in the mock filesystem.
    
    Args:
        ctx: Pydantic AI run context with dependencies
        
    Returns:
        List of file names
    """
    return ctx.deps.get_file_system().ls()


def read_file_tool(
    ctx: RunContext[DeepAgentDependencies],
    file_path: str,
    offset: int = 0,
    limit: int = 2000
) -> str:
    """Read file from the mock filesystem.
    
    Reads a file from the local filesystem. You can access any file directly by using this tool.
    Assume this tool is able to read all files on the machine. If the User provides a path to a file assume that path is valid. It is okay to read a file that does not exist; an error will be returned.

    Usage:
    - The file_path parameter must be an absolute path, not a relative path
    - By default, it reads up to 2000 lines starting from the beginning of the file
    - You can optionally specify a line offset and limit (especially handy for long files), but it's recommended to read the whole file by not providing these parameters
    - Any lines longer than 2000 characters will be truncated
    - Results are returned using cat -n format, with line numbers starting at 1
    - You have the capability to call multiple tools in a single response. It is always better to speculatively read multiple files as a batch that are potentially useful. 
    - If you read a file that exists but has empty contents you will receive a system reminder warning in place of file contents.
    
    Args:
        ctx: Pydantic AI run context with dependencies
        file_path: Path to the file to read
        offset: Line number to start reading from
        limit: Maximum number of lines to read
        
    Returns:
        File contents with line numbers
    """
    return ctx.deps.get_file_system().read_file(file_path, offset, limit)


def write_file_tool(
    ctx: RunContext[DeepAgentDependencies],
    file_path: str,
    content: str
) -> str:
    """Write content to a file in the mock filesystem.
    
    Args:
        ctx: Pydantic AI run context with dependencies
        file_path: Path to the file to write
        content: Content to write to the file
        
    Returns:
        Success message
    """
    return ctx.deps.get_file_system().write_file(file_path, content)


def edit_file_tool(
    ctx: RunContext[DeepAgentDependencies],
    file_path: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False
) -> str:
    """Edit a file in the mock filesystem.
    
    Performs exact string replacements in files. 

    Usage:
    - You must use your `read_file` tool at least once in the conversation before editing. This tool will error if you attempt an edit without reading the file. 
    - When editing text from read_file tool output, ensure you preserve the exact indentation (tabs/spaces) as it appears AFTER the line number prefix. The line number prefix format is: spaces + line number + tab. Everything after that tab is the actual file content to match. Never include any part of the line number prefix in the old_string or new_string.
    - ALWAYS prefer editing existing files. NEVER write new files unless explicitly required.
    - Only use emojis if the user explicitly requests it. Avoid adding emojis to files unless asked.
    - The edit will FAIL if `old_string` is not unique in the file. Either provide a larger string with more surrounding context to make it unique or use `replace_all` to change every instance of `old_string`. 
    - Use `replace_all` for replacing and renaming strings across the file. This parameter is useful if you want to rename a variable for instance.
    
    Args:
        ctx: Pydantic AI run context with dependencies
        file_path: Path to the file to edit
        old_string: String to replace
        new_string: Replacement string
        replace_all: Whether to replace all occurrences
        
    Returns:
        Success message or error description
    """
    return ctx.deps.get_file_system().edit_file(file_path, old_string, new_string, replace_all)


def write_todos_tool(
    ctx: RunContext[DeepAgentDependencies],
    todos: List[Todo]
) -> str:
    """Update the todo list for task management.
    
    Use this tool to create and manage a structured task list for your current work session. This helps you track progress, organize complex tasks, and demonstrate thoroughness to the user.
    It also helps the user understand the progress of the task and overall progress of their requests.

    ## When to Use This Tool
    Use this tool proactively in these scenarios:

    1. Complex multi-step tasks - When a task requires 3 or more distinct steps or actions
    2. Non-trivial and complex tasks - Tasks that require careful planning or multiple operations
    3. User explicitly requests todo list - When the user directly asks you to use the todo list
    4. User provides multiple tasks - When users provide a list of things to be done (numbered or comma-separated)
    5. After receiving new instructions - Immediately capture user requirements as todos
    6. When you start working on a task - Mark it as in_progress BEFORE beginning work. Ideally you should only have one todo as in_progress at a time
    7. After completing a task - Mark it as completed and add any new follow-up tasks discovered during implementation

    ## When NOT to Use This Tool

    Skip using this tool when:
    1. There is only a single, straightforward task
    2. The task is trivial and tracking it provides no organizational benefit
    3. The task can be completed in less than 3 trivial steps
    4. The task is purely conversational or informational

    NOTE that you should not use this tool if there is only one trivial task to do. In this case you are better off just doing the task directly.

    ## Task States and Management

    1. **Task States**: Use these states to track progress:
       - pending: Task not yet started
       - in_progress: Currently working on (limit to ONE task at a time)
       - completed: Task finished successfully

    2. **Task Management**:
       - Update task status in real-time as you work
       - Mark tasks complete IMMEDIATELY after finishing (don't batch completions)
       - Only have ONE task in_progress at any time
       - Complete current tasks before starting new ones
       - Remove tasks that are no longer relevant from the list entirely

    3. **Task Completion Requirements**:
       - ONLY mark a task as completed when you have FULLY accomplished it
       - If you encounter errors, blockers, or cannot finish, keep the task as in_progress
       - When blocked, create a new task describing what needs to be resolved
       - Never mark a task as completed if:
         - There are unresolved issues or errors
         - Work is partial or incomplete
         - You encountered blockers that prevent completion
         - You couldn't find necessary resources or dependencies
         - Quality standards haven't been met

    4. **Task Breakdown**:
       - Create specific, actionable items
       - Break complex tasks into smaller, manageable steps
       - Use clear, descriptive task names

    When in doubt, use this tool. Being proactive with task management demonstrates attentiveness and ensures you complete all requirements successfully.
    
    Args:
        ctx: Pydantic AI run context with dependencies
        todos: List of todo items to set
        
    Returns:
        Success message
    """
    return ctx.deps.get_todo_manager().write_todos(todos)