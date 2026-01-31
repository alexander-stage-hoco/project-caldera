"""Module A: CE Task polling for analysis completion."""

import time
from dataclasses import dataclass
from enum import Enum

import structlog

from .client import SonarQubeClient, SonarQubeApiError

logger = structlog.get_logger(__name__)


class TaskStatus(Enum):
    """SonarQube Compute Engine task statuses."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELED = "CANCELED"

    @property
    def is_terminal(self) -> bool:
        """Check if status is terminal (no further changes expected)."""
        return self in (TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELED)


@dataclass
class TaskResult:
    """Result of a completed analysis task."""

    task_id: str
    analysis_id: str | None
    status: TaskStatus
    component_key: str
    submitted_at: str
    started_at: str | None
    executed_at: str | None
    execution_time_ms: int | None
    error_message: str | None = None
    warning_count: int = 0

    @classmethod
    def from_api_response(cls, data: dict) -> "TaskResult":
        """Create TaskResult from API response."""
        task = data.get("task", data)
        return cls(
            task_id=task.get("id", ""),
            analysis_id=task.get("analysisId"),
            status=TaskStatus(task.get("status", "PENDING")),
            component_key=task.get("componentKey", ""),
            submitted_at=task.get("submittedAt", ""),
            started_at=task.get("startedAt"),
            executed_at=task.get("executedAt"),
            execution_time_ms=task.get("executionTimeMs"),
            error_message=task.get("errorMessage"),
            warning_count=task.get("warningCount", 0),
        )


class AnalysisTimeoutError(Exception):
    """Raised when analysis takes too long to complete."""


class AnalysisFailedError(Exception):
    """Raised when analysis fails."""

    def __init__(self, message: str, task_result: TaskResult | None = None):
        super().__init__(message)
        self.task_result = task_result


def get_task_status(client: SonarQubeClient, task_id: str) -> TaskResult:
    """Get the status of a specific CE task.

    Args:
        client: SonarQube API client
        task_id: The CE task ID

    Returns:
        TaskResult with current status
    """
    data = client.get("/api/ce/task", {"id": task_id})
    return TaskResult.from_api_response(data)


def get_component_pending_tasks(client: SonarQubeClient, component_key: str) -> list[TaskResult]:
    """Get pending tasks for a component.

    Args:
        client: SonarQube API client
        component_key: Project key

    Returns:
        List of pending/in-progress tasks
    """
    data = client.get("/api/ce/component", {"component": component_key})
    tasks = []

    # Current task (if any)
    if current := data.get("current"):
        tasks.append(TaskResult.from_api_response({"task": current}))

    # Queue (pending tasks)
    for task in data.get("queue", []):
        tasks.append(TaskResult.from_api_response({"task": task}))

    return tasks


def find_latest_task(client: SonarQubeClient, component_key: str) -> TaskResult | None:
    """Find the most recent task for a component.

    Args:
        client: SonarQube API client
        component_key: Project key

    Returns:
        Most recent TaskResult or None if no tasks found
    """
    # First check for active/pending tasks
    active_tasks = get_component_pending_tasks(client, component_key)
    if active_tasks:
        return active_tasks[0]  # Most recent first

    # Check activity (completed tasks)
    data = client.get(
        "/api/ce/activity",
        {"component": component_key, "ps": 1, "status": "SUCCESS,FAILED,CANCELED"},
    )

    tasks = data.get("tasks", [])
    if tasks:
        return TaskResult.from_api_response({"task": tasks[0]})

    return None


def wait_for_analysis_complete(
    client: SonarQubeClient,
    component_key: str,
    timeout: int = 600,
    poll_interval: int = 5,
    task_id: str | None = None,
) -> TaskResult:
    """Wait for analysis to complete, polling task status.

    Args:
        client: SonarQube API client
        component_key: Project key
        timeout: Maximum time to wait in seconds
        poll_interval: Time between status checks in seconds
        task_id: Specific task ID to wait for (if known)

    Returns:
        TaskResult with final status

    Raises:
        AnalysisTimeoutError: If analysis doesn't complete within timeout
        AnalysisFailedError: If analysis fails
    """
    logger.info(
        "Waiting for analysis to complete",
        component_key=component_key,
        timeout=timeout,
        task_id=task_id,
    )

    start_time = time.time()
    last_status = None

    while time.time() - start_time < timeout:
        try:
            if task_id:
                result = get_task_status(client, task_id)
            else:
                # Find the latest task for this component
                result = find_latest_task(client, component_key)
                if result is None:
                    logger.debug("No tasks found yet, waiting...")
                    time.sleep(poll_interval)
                    continue

            if result.status != last_status:
                logger.info("Task status", status=result.status.value, task_id=result.task_id)
                last_status = result.status

            if result.status == TaskStatus.SUCCESS:
                logger.info(
                    "Analysis completed successfully",
                    analysis_id=result.analysis_id,
                    execution_time_ms=result.execution_time_ms,
                )
                return result

            if result.status == TaskStatus.FAILED:
                raise AnalysisFailedError(
                    f"Analysis failed: {result.error_message}",
                    task_result=result,
                )

            if result.status == TaskStatus.CANCELED:
                raise AnalysisFailedError(
                    "Analysis was canceled",
                    task_result=result,
                )

        except SonarQubeApiError as e:
            logger.warning("Error checking task status", error=str(e))

        time.sleep(poll_interval)

    raise AnalysisTimeoutError(
        f"Analysis did not complete within {timeout}s"
    )


def get_analysis_warnings(client: SonarQubeClient, task_id: str) -> list[str]:
    """Get warnings from an analysis task.

    Args:
        client: SonarQube API client
        task_id: The CE task ID

    Returns:
        List of warning messages
    """
    try:
        data = client.get("/api/ce/task", {"id": task_id, "additionalFields": "warnings"})
        task = data.get("task", {})
        return task.get("warnings", [])
    except SonarQubeApiError:
        return []
