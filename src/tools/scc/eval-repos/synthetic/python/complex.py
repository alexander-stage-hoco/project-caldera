"""Complex Python module with higher cyclomatic complexity."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum


class Status(Enum):
    """Status enumeration."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """Represents a task with status tracking."""
    id: int
    name: str
    status: Status
    priority: int
    tags: List[str]
    metadata: Optional[Dict[str, Any]] = None


class TaskManager:
    """Manages a collection of tasks with various operations."""

    def __init__(self):
        self.tasks: Dict[int, Task] = {}
        self._next_id = 1

    def create_task(
        self,
        name: str,
        priority: int = 0,
        tags: Optional[List[str]] = None
    ) -> Task:
        """Create a new task."""
        task = Task(
            id=self._next_id,
            name=name,
            status=Status.PENDING,
            priority=priority,
            tags=tags or []
        )
        self.tasks[task.id] = task
        self._next_id += 1
        return task

    def get_task(self, task_id: int) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def update_status(self, task_id: int, status: Status) -> bool:
        """Update task status with validation."""
        task = self.get_task(task_id)
        if task is None:
            return False

        # Status transition validation
        valid_transitions = {
            Status.PENDING: [Status.ACTIVE, Status.FAILED],
            Status.ACTIVE: [Status.COMPLETED, Status.FAILED],
            Status.COMPLETED: [],
            Status.FAILED: [Status.PENDING],
        }

        if status not in valid_transitions.get(task.status, []):
            return False

        task.status = status
        return True

    def filter_by_status(self, status: Status) -> List[Task]:
        """Filter tasks by status."""
        return [t for t in self.tasks.values() if t.status == status]

    def filter_by_priority(self, min_priority: int) -> List[Task]:
        """Filter tasks by minimum priority."""
        return [t for t in self.tasks.values() if t.priority >= min_priority]

    def filter_by_tag(self, tag: str) -> List[Task]:
        """Filter tasks containing a specific tag."""
        return [t for t in self.tasks.values() if tag in t.tags]

    def get_statistics(self) -> Dict[str, Any]:
        """Calculate task statistics."""
        total = len(self.tasks)
        if total == 0:
            return {"total": 0, "by_status": {}, "avg_priority": 0}

        by_status = {}
        for status in Status:
            count = len(self.filter_by_status(status))
            by_status[status.value] = count

        avg_priority = sum(t.priority for t in self.tasks.values()) / total

        return {
            "total": total,
            "by_status": by_status,
            "avg_priority": round(avg_priority, 2),
            "completion_rate": by_status.get("completed", 0) / total if total > 0 else 0
        }

    def bulk_update(self, task_ids: List[int], status: Status) -> Dict[int, bool]:
        """Update multiple tasks at once."""
        results = {}
        for task_id in task_ids:
            results[task_id] = self.update_status(task_id, status)
        return results
