"""
To-do list application with local storage functionality.
Supports CRUD operations, filtering, priority levels, and persistence.
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum
import uuid


class TaskPriority(str, Enum):
    """Priority levels for tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    """Status of a task."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Task:
    """Represents a single to-do task."""
    
    def __init__(
        self,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        due_date: Optional[str] = None,
        task_id: Optional[str] = None,
        status: TaskStatus = TaskStatus.TODO,
        created_at: Optional[str] = None,
        completed_at: Optional[str] = None,
        tags: Optional[List[str]] = None
    ):
        """Initialize a task."""
        self.id = task_id or str(uuid.uuid4())
        self.title = title
        self.description = description
        self.priority = priority if isinstance(priority, TaskPriority) else TaskPriority(priority)
        self.due_date = due_date
        self.status = status if isinstance(status, TaskStatus) else TaskStatus(status)
        self.created_at = created_at or datetime.now().isoformat()
        self.completed_at = completed_at
        self.tags = tags or []
    
    def to_dict(self) -> Dict:
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "due_date": self.due_date,
            "status": self.status.value,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Task":
        """Create task from dictionary."""
        return cls(
            title=data["title"],
            description=data.get("description", ""),
            priority=TaskPriority(data.get("priority", "medium")),
            due_date=data.get("due_date"),
            task_id=data.get("id"),
            status=TaskStatus(data.get("status", "todo")),
            created_at=data.get("created_at"),
            completed_at=data.get("completed_at"),
            tags=data.get("tags", [])
        )


class TodoList:
    """To-do list manager with local storage."""
    
    def __init__(self, storage_path: str = "todo_data.json"):
        """Initialize todo list."""
        self.storage_path = storage_path
        self.tasks: Dict[str, Task] = {}
        self.load_from_storage()
    
    def add_task(
        self,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        due_date: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Task:
        """Add a new task."""
        task = Task(
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            tags=tags or []
        )
        self.tasks[task.id] = task
        self.save_to_storage()
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)
    
    def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[TaskPriority] = None,
        due_date: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[Task]:
        """Update a task."""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if priority is not None:
            task.priority = priority if isinstance(priority, TaskPriority) else TaskPriority(priority)
        if due_date is not None:
            task.due_date = due_date
        if status is not None:
            task.status = status if isinstance(status, TaskStatus) else TaskStatus(status)
            if status == TaskStatus.COMPLETED:
                task.completed_at = datetime.now().isoformat()
            elif status != TaskStatus.COMPLETED:
                task.completed_at = None
        if tags is not None:
            task.tags = tags
        
        self.save_to_storage()
        return task
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.save_to_storage()
            return True
        return False
    
    def mark_completed(self, task_id: str) -> Optional[Task]:
        """Mark a task as completed."""
        return self.update_task(task_id, status=TaskStatus.COMPLETED)
    
    def mark_in_progress(self, task_id: str) -> Optional[Task]:
        """Mark a task as in progress."""
        return self.update_task(task_id, status=TaskStatus.IN_PROGRESS)
    
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks."""
        return list(self.tasks.values())
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get tasks filtered by status."""
        status_enum = status if isinstance(status, TaskStatus) else TaskStatus(status)
        return [task for task in self.tasks.values() if task.status == status_enum]
    
    def get_tasks_by_priority(self, priority: TaskPriority) -> List[Task]:
        """Get tasks filtered by priority."""
        priority_enum = priority if isinstance(priority, TaskPriority) else TaskPriority(priority)
        return [task for task in self.tasks.values() if task.priority == priority_enum]
    
    def get_tasks_by_tag(self, tag: str) -> List[Task]:
        """Get tasks filtered by tag."""
        return [task for task in self.tasks.values() if tag in task.tags]
    
    def get_overdue_tasks(self) -> List[Task]:
        """Get tasks that are overdue."""
        today = datetime.now().date()
        overdue = []
        for task in self.tasks.values():
            if (
                task.status != TaskStatus.COMPLETED
                and task.due_date
                and datetime.fromisoformat(task.due_date).date() < today
            ):
                overdue.append(task)
        return overdue
    
    def get_due_soon_tasks(self, days: int = 7) -> List[Task]:
        """Get tasks due soon."""
        today = datetime.now().date()
        due_soon = []
        for task in self.tasks.values():
            if (
                task.status != TaskStatus.COMPLETED
                and task.due_date
            ):
                due_date = datetime.fromisoformat(task.due_date).date()
                if today <= due_date <= today + timedelta(days=days):
                    due_soon.append(task)
        return sorted(due_soon, key=lambda t: t.due_date)
    
    def search_tasks(self, query: str) -> List[Task]:
        """Search tasks by title or description."""
        query_lower = query.lower()
        return [
            task for task in self.tasks.values()
            if query_lower in task.title.lower() or query_lower in task.description.lower()
        ]
    
    def get_statistics(self) -> Dict:
        """Get statistics about tasks."""
        total = len(self.tasks)
        completed = len(self.get_tasks_by_status(TaskStatus.COMPLETED))
        in_progress = len(self.get_tasks_by_status(TaskStatus.IN_PROGRESS))
        todo = len(self.get_tasks_by_status(TaskStatus.TODO))
        overdue = len(self.get_overdue_tasks())
        
        priority_counts = {}
        for priority in TaskPriority:
            priority_counts[priority.value] = len(self.get_tasks_by_priority(priority))
        
        return {
            "total_tasks": total,
            "completed": completed,
            "in_progress": in_progress,
            "todo": todo,
            "overdue": overdue,
            "completion_rate": (completed / total * 100) if total > 0 else 0,
            "by_priority": priority_counts
        }
    
    def save_to_storage(self) -> bool:
        """Save tasks to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.storage_path) or ".", exist_ok=True)
            
            data = {
                "tasks": [task.to_dict() for task in self.tasks.values()],
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving to storage: {e}")
            return False
    
    def load_from_storage(self) -> bool:
        """Load tasks from JSON file."""
        if not os.path.exists(self.storage_path):
            return False
        
        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
            
            self.tasks = {}
            for task_data in data.get("tasks", []):
                task = Task.from_dict(task_data)
                self.tasks[task.id] = task
            return True
        except Exception as e:
            print(f"Error loading from storage: {e}")
            return False
    
    def clear_all_tasks(self) -> None:
        """Clear all tasks."""
        self.tasks.clear()
        self.save_to_storage()
    
    def export_to_json(self, filepath: str) -> bool:
        """Export tasks to a specific JSON file."""
        try:
            data = {
                "tasks": [task.to_dict() for task in self.tasks.values()],
                "exported_at": datetime.now().isoformat()
            }
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting tasks: {e}")
            return False
    
    def import_from_json(self, filepath: str) -> bool:
        """Import tasks from a JSON file."""
        if not os.path.exists(filepath):
            return False
        
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            
            imported_count = 0
            for task_data in data.get("tasks", []):
                task = Task.from_dict(task_data)
                if task.id not in self.tasks:
                    self.tasks[task.id] = task
                    imported_count += 1
            
            if imported_count > 0:
                self.save_to_storage()
            return True
        except Exception as e:
            print(f"Error importing tasks: {e}")
            return False
