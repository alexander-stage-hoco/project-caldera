"""Tests for EvidenceCollector with mock fetcher."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from insights.evidence.collector import EvidenceCollector


class TestEvidenceCollector:
    def _make_fetcher(self, query_results: dict[str, list[dict]] | None = None) -> MagicMock:
        fetcher = MagicMock()
        results = query_results or {}

        def mock_fetch(query_name: str, run_pk: int, **kwargs):
            return results.get(query_name, [])

        fetcher.fetch.side_effect = mock_fetch
        return fetcher

    def test_collect_empty(self):
        collector = EvidenceCollector()
        fetcher = self._make_fetcher()
        items = collector.collect(fetcher, run_pk=1)
        assert items == []

    def test_collect_complexity(self):
        collector = EvidenceCollector()
        fetcher = self._make_fetcher({
            "evidence_complexity": [
                {
                    "relative_path": "src/heavy.py",
                    "loc_total": 500,
                    "max_ccn": 25,
                    "total_ccn": 100,
                    "function_count": 10,
                    "avg_ccn": 10.0,
                    "tool_run_pk": 2,
                },
            ],
        })
        items = collector.collect(fetcher, run_pk=1)
        assert len(items) >= 1
        ccn_items = [i for i in items if i.category == "complexity"]
        assert len(ccn_items) == 1
        assert ccn_items[0].evidence_id == "E-CCN-001"
        assert ccn_items[0].location == "src/heavy.py"
        assert ccn_items[0].tool_source == "lizard"

    def test_collect_security_cve(self):
        collector = EvidenceCollector()
        fetcher = self._make_fetcher({
            "evidence_security": [
                {
                    "finding_type": "cve",
                    "location": "package.json",
                    "finding_id": "CVE-2024-1234",
                    "severity": "CRITICAL",
                    "description": "RCE vulnerability",
                    "package_name": "evil-pkg",
                    "installed_version": "1.0.0",
                    "fixed_version": "1.0.1",
                    "tool_run_pk": 3,
                },
            ],
        })
        items = collector.collect(fetcher, run_pk=1)
        sec_items = [i for i in items if i.category == "security"]
        assert len(sec_items) == 1
        assert sec_items[0].evidence_type == "vulnerability"
        assert "CVE-2024-1234" in sec_items[0].excerpt

    def test_collect_security_secret(self):
        collector = EvidenceCollector()
        fetcher = self._make_fetcher({
            "evidence_security": [
                {
                    "finding_type": "secret",
                    "location": "config.py",
                    "finding_id": "generic-api-key",
                    "severity": "CRITICAL",
                    "description": "Generic API Key",
                    "package_name": None,
                    "installed_version": None,
                    "fixed_version": None,
                    "tool_run_pk": 4,
                },
            ],
        })
        items = collector.collect(fetcher, run_pk=1)
        sec_items = [i for i in items if i.category == "security"]
        assert len(sec_items) == 1
        assert sec_items[0].evidence_type == "secret_detection"

    def test_collect_coupling(self):
        collector = EvidenceCollector()
        fetcher = self._make_fetcher({
            "evidence_coupling": [
                {
                    "symbol_name": "DbService",
                    "symbol_type": "class",
                    "relative_path": "src/db.py",
                    "fan_in": 5,
                    "fan_out": 30,
                    "total_coupling": 35,
                    "instability": 0.86,
                    "coupling_risk": "critical",
                    "coupling_pattern": "unstable_dependency",
                    "tool_run_pk": 5,
                },
            ],
        })
        items = collector.collect(fetcher, run_pk=1)
        coup_items = [i for i in items if i.category == "coupling"]
        assert len(coup_items) == 1
        assert coup_items[0].evidence_id == "E-COUP-001"

    def test_collect_graceful_on_query_failure(self):
        collector = EvidenceCollector()
        fetcher = MagicMock()
        fetcher.fetch.side_effect = Exception("DB error")

        # Should not raise; returns empty list
        items = collector.collect(fetcher, run_pk=1)
        assert items == []

    def test_collect_all_categories(self):
        """Verify all 6 categories are attempted."""
        collector = EvidenceCollector()
        fetcher = self._make_fetcher({
            "evidence_complexity": [{"relative_path": "a.py", "loc_total": 100, "max_ccn": 20, "total_ccn": 20, "function_count": 2, "avg_ccn": 10.0, "tool_run_pk": 1}],
            "evidence_security": [{"finding_type": "cve", "location": "b.py", "finding_id": "CVE-1", "severity": "HIGH", "description": "vuln", "package_name": "pkg", "installed_version": "1", "fixed_version": "2", "tool_run_pk": 1}],
            "evidence_coupling": [{"symbol_name": "X", "symbol_type": "class", "relative_path": "c.py", "fan_in": 1, "fan_out": 10, "total_coupling": 11, "instability": 0.9, "coupling_risk": "high", "coupling_pattern": "hub", "tool_run_pk": 1}],
            "evidence_coverage": [{"relative_path": "d.py", "loc_total": 200, "max_ccn": 20, "total_ccn": 20, "function_count": 3, "line_coverage_pct": 20, "branch_coverage_pct": 10, "tool_run_pk": 1}],
            "evidence_ownership": [{"relative_path": "e.py", "unique_authors": 1, "top_author": "dev", "top_author_pct": 100, "total_lines": 600, "risk_level": "critical", "tool_run_pk": 1}],
            "evidence_quality": [{"relative_path": "f.py", "loc_total": 200, "smell_count": 10, "issue_count": 5, "smell_density_per_kloc": 50, "issue_density_per_kloc": 25, "tool_run_pk": 1}],
        })
        items = collector.collect(fetcher, run_pk=1)
        categories = {i.category for i in items}
        assert categories == {"complexity", "security", "coupling", "coverage", "ownership", "quality"}
