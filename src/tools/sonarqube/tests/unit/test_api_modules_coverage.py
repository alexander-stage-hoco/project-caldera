"""Tests targeting uncovered paths in API modules for coverage improvement."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from scripts.api.module_a_task import TaskResult, TaskStatus, find_latest_task, get_component_pending_tasks
from scripts.api.module_b_components import (
    Component,
    ComponentQualifier,
    ComponentTree,
)
from scripts.api.module_h_quality_gate import (
    QualityGateCondition,
    QualityGateResult,
    QualityGateStatus,
    ConditionStatus,
    _conditions_from_definition,
)
from scripts.api.module_i_history import (
    AnalysisEvent,
    Analysis,
    AnalysisHistory,
)


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_is_terminal_success(self) -> None:
        assert TaskStatus.SUCCESS.is_terminal is True

    def test_is_terminal_failed(self) -> None:
        assert TaskStatus.FAILED.is_terminal is True

    def test_is_terminal_canceled(self) -> None:
        assert TaskStatus.CANCELED.is_terminal is True

    def test_not_terminal_pending(self) -> None:
        assert TaskStatus.PENDING.is_terminal is False

    def test_not_terminal_in_progress(self) -> None:
        assert TaskStatus.IN_PROGRESS.is_terminal is False


class TestTaskResultFromApi:
    """Tests for TaskResult.from_api_response."""

    def test_basic_task(self) -> None:
        data = {
            "task": {
                "id": "task-1",
                "analysisId": "analysis-1",
                "status": "SUCCESS",
                "componentKey": "my-project",
                "submittedAt": "2025-01-01T00:00:00Z",
                "startedAt": "2025-01-01T00:00:01Z",
                "executedAt": "2025-01-01T00:00:10Z",
                "executionTimeMs": 9000,
            }
        }
        result = TaskResult.from_api_response(data)
        assert result.task_id == "task-1"
        assert result.status == TaskStatus.SUCCESS
        assert result.analysis_id == "analysis-1"

    def test_failed_task_with_error(self) -> None:
        data = {
            "task": {
                "id": "task-2",
                "status": "FAILED",
                "componentKey": "my-project",
                "submittedAt": "2025-01-01T00:00:00Z",
                "errorMessage": "Analysis failed",
            }
        }
        result = TaskResult.from_api_response(data)
        assert result.status == TaskStatus.FAILED
        assert result.error_message == "Analysis failed"


class TestGetComponentPendingTasks:
    """Tests for pending task retrieval."""

    def test_no_tasks(self) -> None:
        client = MagicMock()
        client.get.return_value = {}
        tasks = get_component_pending_tasks(client, "my-project")
        assert tasks == []

    def test_with_current_task(self) -> None:
        client = MagicMock()
        client.get.return_value = {
            "current": {
                "id": "task-1",
                "status": "IN_PROGRESS",
                "componentKey": "my-project",
                "submittedAt": "2025-01-01T00:00:00Z",
            },
            "queue": [],
        }
        tasks = get_component_pending_tasks(client, "my-project")
        assert len(tasks) == 1
        assert tasks[0].status == TaskStatus.IN_PROGRESS

    def test_with_queued_tasks(self) -> None:
        client = MagicMock()
        client.get.return_value = {
            "queue": [
                {
                    "id": "task-2",
                    "status": "PENDING",
                    "componentKey": "my-project",
                    "submittedAt": "2025-01-01T00:00:00Z",
                },
            ]
        }
        tasks = get_component_pending_tasks(client, "my-project")
        assert len(tasks) == 1


class TestFindLatestTask:
    """Tests for finding the most recent task."""

    def test_no_tasks_returns_none(self) -> None:
        client = MagicMock()
        client.get.side_effect = [
            {},  # component pending tasks
            {"tasks": []},  # activity
        ]
        result = find_latest_task(client, "my-project")
        assert result is None

    def test_finds_active_task(self) -> None:
        client = MagicMock()
        client.get.side_effect = [
            {
                "current": {
                    "id": "task-active",
                    "status": "IN_PROGRESS",
                    "componentKey": "my-project",
                    "submittedAt": "2025-01-01",
                },
            },
        ]
        result = find_latest_task(client, "my-project")
        assert result is not None
        assert result.task_id == "task-active"

    def test_finds_completed_task(self) -> None:
        client = MagicMock()
        client.get.side_effect = [
            {},  # No pending
            {
                "tasks": [
                    {
                        "id": "task-done",
                        "status": "SUCCESS",
                        "componentKey": "my-project",
                        "submittedAt": "2025-01-01",
                    }
                ]
            },
        ]
        result = find_latest_task(client, "my-project")
        assert result is not None
        assert result.task_id == "task-done"


class TestQualityGateCondition:
    """Tests for quality gate condition parsing."""

    def test_from_api_response(self) -> None:
        data = {
            "metricKey": "new_coverage",
            "comparator": "LT",
            "errorThreshold": "80",
            "status": "ERROR",
            "actualValue": "65.2",
        }
        cond = QualityGateCondition.from_api_response(data)
        assert cond.metric == "new_coverage"
        assert cond.status == ConditionStatus.ERROR
        assert cond.actual_value == "65.2"

    def test_to_dict(self) -> None:
        cond = QualityGateCondition(
            metric="coverage", comparator="LT",
            threshold="80", status=ConditionStatus.OK,
            actual_value="90", error_threshold="80",
        )
        d = cond.to_dict()
        assert d["metric"] == "coverage"
        assert d["status"] == "OK"


class TestQualityGateResult:
    """Tests for quality gate result parsing."""

    def test_from_api_response(self) -> None:
        data = {
            "projectStatus": {
                "status": "OK",
                "conditions": [
                    {
                        "metricKey": "coverage",
                        "comparator": "LT",
                        "errorThreshold": "80",
                        "status": "OK",
                        "actualValue": "85.3",
                    },
                ],
            }
        }
        result = QualityGateResult.from_api_response(data)
        assert result.status == QualityGateStatus.OK
        assert len(result.conditions) == 1

    def test_failed_and_warning_conditions(self) -> None:
        result = QualityGateResult(
            status=QualityGateStatus.ERROR,
            conditions=[
                QualityGateCondition(
                    metric="coverage", comparator="LT",
                    threshold="80", status=ConditionStatus.ERROR,
                ),
                QualityGateCondition(
                    metric="duplications", comparator="GT",
                    threshold="3", status=ConditionStatus.WARN,
                ),
                QualityGateCondition(
                    metric="reliability", comparator="GT",
                    threshold="1", status=ConditionStatus.OK,
                ),
            ],
        )
        assert len(result.failed_conditions) == 1
        assert len(result.warning_conditions) == 1

    def test_to_dict(self) -> None:
        result = QualityGateResult(
            status=QualityGateStatus.OK,
            name="Default",
            conditions=[],
        )
        d = result.to_dict()
        assert d["status"] == "OK"
        assert d["failed_count"] == 0


class TestConditionsFromDefinition:
    """Tests for _conditions_from_definition helper."""

    def test_parses_definition_conditions(self) -> None:
        definition = {
            "conditions": [
                {"metric": "coverage", "op": "LT", "error": "80"},
                {"metricKey": "duplications", "comparator": "GT", "errorThreshold": "3"},
            ],
        }
        conds = _conditions_from_definition(definition)
        assert len(conds) == 2
        assert conds[0].metric == "coverage"
        assert conds[1].metric == "duplications"

    def test_empty_definition(self) -> None:
        assert _conditions_from_definition({}) == []


class TestAnalysis:
    """Tests for Analysis data class."""

    def test_from_api_response(self) -> None:
        data = {
            "key": "analysis-1",
            "date": "2025-01-01T00:00:00+0000",
            "projectVersion": "1.0.0",
            "revision": "abc123",
            "events": [
                {"key": "e1", "category": "VERSION", "name": "1.0.0"},
            ],
        }
        analysis = Analysis.from_api_response(data)
        assert analysis.key == "analysis-1"
        assert analysis.project_version == "1.0.0"
        assert len(analysis.events) == 1

    def test_parsed_date(self) -> None:
        analysis = Analysis(key="a", date="2025-01-01T00:00:00+00:00")
        assert analysis.parsed_date is not None

    def test_parsed_date_invalid(self) -> None:
        analysis = Analysis(key="a", date="not-a-date")
        assert analysis.parsed_date is None

    def test_to_dict(self) -> None:
        analysis = Analysis(
            key="a", date="2025-01-01",
            project_version="1.0", revision="abc",
        )
        d = analysis.to_dict()
        assert d["project_version"] == "1.0"
        assert d["revision"] == "abc"


class TestAnalysisEvent:
    """Tests for AnalysisEvent data class."""

    def test_from_api_response(self) -> None:
        data = {"key": "e1", "category": "VERSION", "name": "1.0.0", "description": "Release"}
        event = AnalysisEvent.from_api_response(data)
        assert event.category == "VERSION"
        assert event.description == "Release"

    def test_to_dict_with_description(self) -> None:
        event = AnalysisEvent(key="e1", category="VERSION", name="1.0", description="desc")
        d = event.to_dict()
        assert d["description"] == "desc"

    def test_to_dict_without_description(self) -> None:
        event = AnalysisEvent(key="e1", category="VERSION", name="1.0")
        d = event.to_dict()
        assert "description" not in d


class TestComponentQualifier:
    """Tests for ComponentQualifier enum."""

    def test_from_string_known(self) -> None:
        assert ComponentQualifier.from_string("TRK") == ComponentQualifier.PROJECT
        assert ComponentQualifier.from_string("DIR") == ComponentQualifier.DIRECTORY
        assert ComponentQualifier.from_string("FIL") == ComponentQualifier.FILE

    def test_from_string_unknown(self) -> None:
        assert ComponentQualifier.from_string("XYZ") == ComponentQualifier.FILE


class TestComponent:
    """Tests for Component data class."""

    def test_from_api_response(self) -> None:
        data = {
            "key": "project:src/main.py",
            "name": "main.py",
            "qualifier": "FIL",
            "path": "src/main.py",
            "language": "py",
        }
        comp = Component.from_api_response(data)
        assert comp.key == "project:src/main.py"
        assert comp.qualifier == ComponentQualifier.FILE
        assert comp.language == "py"

    def test_to_dict_full(self) -> None:
        comp = Component(
            key="k", name="n",
            qualifier=ComponentQualifier.FILE,
            path="src/file.py", language="py",
            measures={"coverage": 80},
        )
        d = comp.to_dict()
        assert d["path"] == "src/file.py"
        assert d["language"] == "py"
        assert d["measures"]["coverage"] == 80

    def test_to_dict_minimal(self) -> None:
        comp = Component(key="k", name="n", qualifier=ComponentQualifier.FILE)
        d = comp.to_dict()
        assert "path" not in d
        assert "language" not in d


class TestComponentTree:
    """Tests for ComponentTree data class."""

    def test_files_property(self) -> None:
        root = Component(key="root", name="project", qualifier=ComponentQualifier.PROJECT)
        file1 = Component(key="f1", name="a.py", qualifier=ComponentQualifier.FILE)
        dir1 = Component(key="d1", name="src", qualifier=ComponentQualifier.DIRECTORY)
        tree = ComponentTree(
            root=root,
            by_key={"root": root, "f1": file1, "d1": dir1},
        )
        assert len(tree.files) == 1
        assert len(tree.directories) == 1

    def test_get_children(self) -> None:
        root = Component(key="root", name="project", qualifier=ComponentQualifier.PROJECT)
        child = Component(key="c1", name="child", qualifier=ComponentQualifier.FILE)
        tree = ComponentTree(
            root=root,
            by_key={"root": root, "c1": child},
            children={"root": ["c1"]},
        )
        children = tree.get_children("root")
        assert len(children) == 1
        assert children[0].key == "c1"

    def test_to_dict(self) -> None:
        root = Component(key="root", name="project", qualifier=ComponentQualifier.PROJECT)
        tree = ComponentTree(root=root, by_key={"root": root})
        d = tree.to_dict()
        assert d["root_key"] == "root"
