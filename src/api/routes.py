"""
FastAPI endpoints for timezone clock and todo list applications.
Provides REST API access to both utilities.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict
from datetime import datetime

from src.utils.timezone_clock import DigitalClock, TimezoneInfo
from src.utils.todo_list import TodoList, Task, TaskPriority, TaskStatus

# Initialize routers
clock_router = APIRouter(prefix="/clock", tags=["Clock"])
todo_router = APIRouter(prefix="/todos", tags=["Todo"])

# Initialize utilities
digital_clock = DigitalClock()
todo_list = TodoList("storage/todos.json")


# ============= TIMEZONE CLOCK ENDPOINTS =============

@clock_router.get("/timezones")
def get_all_timezones() -> Dict:
    """
    Get all available timezones with their current times.
    
    Returns:
        Dictionary with all timezone information and current times
    """
    return digital_clock.get_all_times()


@clock_router.get("/time/{timezone_name}")
def get_timezone_time(timezone_name: str) -> Dict:
    """
    Get current time in a specific timezone.
    
    Args:
        timezone_name: Name of the timezone (e.g., "New York", "London")
    
    Returns:
        Current time, date, offset, and timezone info
    """
    try:
        time_str, offset, date_str = digital_clock.get_time(timezone_name)
        return {
            "timezone": timezone_name,
            "time": time_str,
            "date": date_str,
            "offset": offset,
            "timestamp": datetime.now().isoformat()
        }
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Timezone '{timezone_name}' not found. Use /clock/timezones to see available timezones."
        )


@clock_router.get("/table")
def get_timezones_table() -> Dict:
    """
    Get all timezones in formatted table view.
    
    Returns:
        Formatted table string representation
    """
    return {
        "table": digital_clock.display_table(),
        "timezones": list(digital_clock.timezones.keys()),
        "count": len(digital_clock.timezones)
    }


@clock_router.post("/add/{timezone_name}/{timezone_str}")
def add_timezone(timezone_name: str, timezone_str: str) -> Dict:
    """
    Add a new timezone to the clock.
    
    Args:
        timezone_name: Display name for the timezone
        timezone_str: Timezone string (e.g., "America/New_York")
    
    Returns:
        Success message with timezone info
    """
    try:
        digital_clock.add_timezone(timezone_name, timezone_str)
        return {
            "status": "success",
            "message": f"Added timezone: {timezone_name}",
            "timezone": timezone_name,
            "timezone_str": timezone_str
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@clock_router.delete("/remove/{timezone_name}")
def remove_timezone(timezone_name: str) -> Dict:
    """
    Remove a timezone from the clock.
    
    Args:
        timezone_name: Name of the timezone to remove
    
    Returns:
        Success message
    """
    if timezone_name not in digital_clock.timezones:
        raise HTTPException(status_code=404, detail=f"Timezone not found: {timezone_name}")
    
    digital_clock.remove_timezone(timezone_name)
    return {
        "status": "success",
        "message": f"Removed timezone: {timezone_name}"
    }


@clock_router.get("/compare")
def compare_timezones(
    tz1: str = Query(..., description="First timezone name"),
    tz2: str = Query(..., description="Second timezone name")
) -> Dict:
    """
    Compare times between two timezones.
    
    Args:
        tz1: First timezone name
        tz2: Second timezone name
    
    Returns:
        Comparison of times and offsets
    """
    try:
        return digital_clock.compare_times(tz1, tz2)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@clock_router.get("/noon-sunset/{timezone_name}")
def get_noon_sunset(timezone_name: str) -> Dict:
    """
    Get approximate noon and sunset times for a timezone.
    
    Args:
        timezone_name: Name of the timezone
    
    Returns:
        Next noon and sunset times
    """
    try:
        return digital_clock.get_noon_sunset_times(timezone_name)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Timezone not found: {timezone_name}"
        )


@clock_router.get("/list")
def list_timezones() -> Dict:
    """
    Get list of all available timezones.
    
    Returns:
        List of timezone names and details
    """
    timezones = []
    for name, tz_info in digital_clock.timezones.items():
        timezones.append({
            "name": name,
            "timezone_str": tz_info.timezone_str,
            "offset": tz_info.offset
        })
    
    return {
        "count": len(timezones),
        "timezones": sorted(timezones, key=lambda x: x["name"])
    }


# ============= TODO LIST ENDPOINTS =============

@todo_router.post("/create")
def create_todo(
    title: str = Query(..., description="Task title"),
    description: str = Query(default="", description="Task description"),
    priority: str = Query(default="medium", description="Task priority"),
    due_date: Optional[str] = Query(default=None, description="Due date (YYYY-MM-DD)"),
    tags: Optional[List[str]] = Query(default=None, description="Task tags")
) -> Dict:
    """
    Create a new todo task.
    
    Args:
        title: Task title
        description: Task description
        priority: Priority level (low, medium, high, urgent)
        due_date: Due date in YYYY-MM-DD format
        tags: List of tags
    
    Returns:
        Created task
    """
    try:
        task = todo_list.add_task(
            title=title,
            description=description,
            priority=TaskPriority(priority),
            due_date=due_date,
            tags=tags
        )
        return task.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@todo_router.get("/")
def get_all_todos(
    status: Optional[str] = Query(default=None, description="Filter by status"),
    priority: Optional[str] = Query(default=None, description="Filter by priority"),
    tag: Optional[str] = Query(default=None, description="Filter by tag")
) -> Dict:
    """
    Get all todos with optional filtering.
    
    Args:
        status: Filter by status (todo, in_progress, completed, cancelled)
        priority: Filter by priority (low, medium, high, urgent)
        tag: Filter by tag
    
    Returns:
        List of tasks
    """
    if status:
        try:
            tasks = todo_list.get_tasks_by_status(TaskStatus(status))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    elif priority:
        try:
            tasks = todo_list.get_tasks_by_priority(TaskPriority(priority))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid priority: {priority}")
    elif tag:
        tasks = todo_list.get_tasks_by_tag(tag)
    else:
        tasks = todo_list.get_all_tasks()
    
    return {
        "count": len(tasks),
        "tasks": [task.to_dict() for task in tasks]
    }


@todo_router.get("/{task_id}")
def get_todo(task_id: str) -> Dict:
    """
    Get a specific todo task.
    
    Args:
        task_id: Task ID
    
    Returns:
        Task details
    """
    task = todo_list.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    return task.to_dict()


@todo_router.put("/{task_id}")
def update_todo(
    task_id: str,
    title: Optional[str] = Query(default=None),
    description: Optional[str] = Query(default=None),
    priority: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    due_date: Optional[str] = Query(default=None),
    tags: Optional[List[str]] = Query(default=None)
) -> Dict:
    """
    Update a todo task.
    
    Args:
        task_id: Task ID
        title: New title
        description: New description
        priority: New priority
        status: New status
        due_date: New due date
        tags: New tags
    
    Returns:
        Updated task
    """
    try:
        priority_enum = TaskPriority(priority) if priority else None
        status_enum = TaskStatus(status) if status else None
        
        task = todo_list.update_task(
            task_id,
            title=title,
            description=description,
            priority=priority_enum,
            status=status_enum,
            due_date=due_date,
            tags=tags
        )
        
        if not task:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
        
        return task.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@todo_router.delete("/{task_id}")
def delete_todo(task_id: str) -> Dict:
    """
    Delete a todo task.
    
    Args:
        task_id: Task ID
    
    Returns:
        Success message
    """
    if not todo_list.delete_task(task_id):
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
    return {
        "status": "success",
        "message": f"Task deleted: {task_id}"
    }


@todo_router.put("/{task_id}/complete")
def complete_todo(task_id: str) -> Dict:
    """
    Mark a todo task as completed.
    
    Args:
        task_id: Task ID
    
    Returns:
        Updated task
    """
    task = todo_list.mark_completed(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
    return task.to_dict()


@todo_router.put("/{task_id}/in-progress")
def start_todo(task_id: str) -> Dict:
    """
    Mark a todo task as in progress.
    
    Args:
        task_id: Task ID
    
    Returns:
        Updated task
    """
    task = todo_list.mark_in_progress(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
    return task.to_dict()


@todo_router.get("/search/query")
def search_todos(q: str = Query(..., description="Search query")) -> Dict:
    """
    Search todos by title or description.
    
    Args:
        q: Search query
    
    Returns:
        Matching tasks
    """
    tasks = todo_list.search_tasks(q)
    return {
        "query": q,
        "count": len(tasks),
        "tasks": [task.to_dict() for task in tasks]
    }


@todo_router.get("/overdue/tasks")
def get_overdue_todos() -> Dict:
    """
    Get all overdue tasks.
    
    Returns:
        List of overdue tasks
    """
    tasks = todo_list.get_overdue_tasks()
    return {
        "count": len(tasks),
        "tasks": [task.to_dict() for task in tasks]
    }


@todo_router.get("/due-soon/tasks")
def get_due_soon_todos(days: int = Query(default=7, ge=1, le=365)) -> Dict:
    """
    Get tasks due soon.
    
    Args:
        days: Number of days to look ahead
    
    Returns:
        List of tasks due soon
    """
    tasks = todo_list.get_due_soon_tasks(days)
    return {
        "days_ahead": days,
        "count": len(tasks),
        "tasks": [task.to_dict() for task in tasks]
    }


@todo_router.get("/statistics")
def get_todo_statistics() -> Dict:
    """
    Get todo list statistics.
    
    Returns:
        Statistics about tasks
    """
    return todo_list.get_statistics()


@todo_router.delete("/clear")
def clear_all_todos() -> Dict:
    """
    Clear all todo tasks.
    
    Returns:
        Success message
    """
    todo_list.clear_all_tasks()
    return {
        "status": "success",
        "message": "All tasks cleared"
    }
