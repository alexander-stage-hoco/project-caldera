"""
Pytest configuration and fixtures for roslyn-analyzers tests.
"""
import json
import sys
from pathlib import Path

import pytest

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


@pytest.fixture
def sample_sarif_v21():
    """Sample SARIF 2.1 format data."""
    return {
        "version": "2.1.0",
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Microsoft.NET.Sdk",
                        "version": "8.0.0",
                        "rules": [
                            {
                                "id": "CA3001",
                                "helpUri": "https://learn.microsoft.com/dotnet/fundamentals/code-analysis/quality-rules/ca3001"
                            },
                            {
                                "id": "CA1001",
                                "helpUri": "https://learn.microsoft.com/dotnet/fundamentals/code-analysis/quality-rules/ca1001"
                            }
                        ]
                    }
                },
                "results": [
                    {
                        "ruleId": "CA3001",
                        "level": "warning",
                        "message": {"text": "SQL injection vulnerability"},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {
                                        "uri": "file:///project/src/security/sql_injection.cs"
                                    },
                                    "region": {
                                        "startLine": 15,
                                        "endLine": 15,
                                        "startColumn": 5,
                                        "endColumn": 50
                                    }
                                }
                            }
                        ]
                    },
                    {
                        "ruleId": "CA1001",
                        "level": "error",
                        "message": {"text": "Types that own disposable fields should be disposable"},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {
                                        "uri": "file:///project/src/resource/missing_idisposable.cs"
                                    },
                                    "region": {
                                        "startLine": 13,
                                        "endLine": 13,
                                        "startColumn": 1,
                                        "endColumn": 20
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_sarif_v1():
    """Sample SARIF 1.0 format data."""
    return {
        "version": "1.0.0",
        "runs": [
            {
                "tool": {
                    "name": "Microsoft.NET.Sdk"
                },
                "results": [
                    {
                        "ruleId": "CA5350",
                        "level": "warning",
                        "message": "Do not use weak cryptographic algorithms",
                        "locations": [
                            {
                                "resultFile": {
                                    "uri": "file:///project/src/security/weak_crypto.cs",
                                    "region": {
                                        "startLine": 16,
                                        "endLine": 16,
                                        "startColumn": 10,
                                        "endColumn": 35
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_analysis_results():
    """Sample analysis results in the standard output format."""
    return {
        "schema_version": "1.0.0",
        "generated_at": "2026-01-22T10:00:00Z",
        "repo_name": "synthetic",
        "repo_path": "/tmp/synthetic",
        "results": {
            "tool": "roslyn-analyzers",
            "tool_version": "1.0.0",
            "analysis_duration_ms": 1234,
            "summary": {
                "total_files_analyzed": 5,
                "total_violations": 10,
                "files_with_violations": 3,
                "violations_by_category": {
                    "security": 4,
                    "resource": 3,
                    "design": 2,
                    "dead_code": 1
                },
                "violations_by_severity": {
                    "critical": 2,
                    "high": 5,
                    "medium": 3
                }
            },
            "files": [
                {
                    "path": "src/security/sql_injection.cs",
                    "relative_path": "src/security/sql_injection.cs",
                    "language": "csharp",
                    "lines_of_code": 100,
                    "violation_count": 3,
                    "violations": [
                        {
                            "rule_id": "CA3001",
                            "dd_category": "security",
                            "dd_severity": "high",
                            "line_start": 15,
                            "message": "SQL injection"
                        },
                        {
                            "rule_id": "CA3001",
                            "dd_category": "security",
                            "dd_severity": "high",
                            "line_start": 28,
                            "message": "SQL injection"
                        },
                        {
                            "rule_id": "CA2100",
                            "dd_category": "security",
                            "dd_severity": "high",
                            "line_start": 39,
                            "message": "Review SQL queries"
                        }
                    ]
                },
                {
                    "path": "src/resource/missing_idisposable.cs",
                    "relative_path": "src/resource/missing_idisposable.cs",
                    "language": "csharp",
                    "lines_of_code": 80,
                    "violation_count": 2,
                    "violations": [
                        {
                            "rule_id": "CA1001",
                            "dd_category": "resource",
                            "dd_severity": "critical",
                            "line_start": 13,
                            "message": "Missing IDisposable"
                        },
                        {
                            "rule_id": "CA1001",
                            "dd_category": "resource",
                            "dd_severity": "critical",
                            "line_start": 32,
                            "message": "Missing IDisposable"
                        }
                    ]
                },
                {
                    "path": "src/design/empty_interfaces.cs",
                    "relative_path": "src/design/empty_interfaces.cs",
                    "language": "csharp",
                    "lines_of_code": 50,
                    "violation_count": 2,
                    "violations": [
                        {
                            "rule_id": "CA1040",
                            "dd_category": "design",
                            "dd_severity": "medium",
                            "line_start": 11,
                            "message": "Empty interface"
                        },
                        {
                            "rule_id": "CA1040",
                            "dd_category": "design",
                            "dd_severity": "medium",
                            "line_start": 16,
                            "message": "Empty interface"
                        }
                    ]
                },
                {
                    "path": "src/clean/clean_service.cs",
                    "relative_path": "src/clean/clean_service.cs",
                    "language": "csharp",
                    "lines_of_code": 60,
                    "violation_count": 0,
                    "violations": []
                },
                {
                    "path": "utils/helpers.cs",
                    "relative_path": "utils/helpers.cs",
                    "language": "csharp",
                    "lines_of_code": 40,
                    "violation_count": 3,
                    "violations": [
                        {
                            "rule_id": "IDE0060",
                            "dd_category": "dead_code",
                            "dd_severity": "medium",
                            "line_start": 5,
                            "message": "Unused parameter"
                        },
                        {
                            "rule_id": "CA1822",
                            "dd_category": "performance",
                            "dd_severity": "low",
                            "line_start": 12,
                            "message": "Mark as static"
                        },
                        {
                            "rule_id": "CA2000",
                            "dd_category": "resource",
                            "dd_severity": "high",
                            "line_start": 25,
                            "message": "Undisposed object"
                        }
                    ]
                }
            ],
            "statistics": {
                "violations_per_file": {
                    "mean": 2.0,
                    "median": 2.0,
                    "min": 0,
                    "max": 3
                },
                "violations_per_1000_loc": 30.3
            },
            "directory_rollup": []
        }
    }


@pytest.fixture
def sample_ground_truth():
    """Sample ground truth data."""
    return {
        "schema_version": "1.0",
        "scenario": "test",
        "expected": {
            "summary": {
                "total_files": 5,
                "total_expected_violations": 10
            },
            "thresholds": {
                "precision_min": 0.85,
                "recall_min": 0.80
            }
        },
        "files": {
            "security/sql_injection.cs": {
                "expected_violations": [
                    {"rule_id": "CA3001", "count": 3, "lines": [15, 28, 39]},
                    {"rule_id": "CA2100", "count": 2, "lines": [50, 62]}
                ],
                "total_expected": 5
            },
            "resource/missing_idisposable.cs": {
                "expected_violations": [
                    {"rule_id": "CA1001", "count": 4, "lines": [13, 32, 53, 74]}
                ],
                "total_expected": 4
            }
        }
    }


@pytest.fixture
def temp_sarif_file(tmp_path, sample_sarif_v21):
    """Create a temporary SARIF file."""
    sarif_path = tmp_path / "test.sarif"
    sarif_path.write_text(json.dumps(sample_sarif_v21))
    return sarif_path
