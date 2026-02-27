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
                    "complexity_max": 25,
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

    def test_multiple_items_per_category_sequential_ids(self):
        """3 complexity rows → 3 evidence items with IDs E-CCN-001..003."""
        collector = EvidenceCollector()
        fetcher = self._make_fetcher({
            "evidence_complexity": [
                {"relative_path": "a.py", "loc_total": 100, "complexity_max": 20, "function_count": 5, "tool_run_pk": 1},
                {"relative_path": "b.py", "loc_total": 200, "complexity_max": 30, "function_count": 8, "tool_run_pk": 1},
                {"relative_path": "c.py", "loc_total": 300, "complexity_max": 40, "function_count": 12, "tool_run_pk": 1},
            ],
        })
        items = collector.collect(fetcher, run_pk=1)
        ccn_items = [i for i in items if i.category == "complexity"]
        assert len(ccn_items) == 3
        assert ccn_items[0].evidence_id == "E-CCN-001"
        assert ccn_items[1].evidence_id == "E-CCN-002"
        assert ccn_items[2].evidence_id == "E-CCN-003"

    def test_null_field_handling(self):
        """Row with max_ccn=None → evidence still created (graceful handling)."""
        collector = EvidenceCollector()
        fetcher = self._make_fetcher({
            "evidence_complexity": [
                {"relative_path": "null.py", "loc_total": None, "complexity_max": None, "function_count": None, "tool_run_pk": 1},
            ],
        })
        items = collector.collect(fetcher, run_pk=1)
        assert len(items) == 1
        # .get() returns None (not default) when key exists with None value
        assert items[0].evidence_id == "E-CCN-001"
        assert items[0].location == "null.py"

    def test_mixed_security_types(self):
        """2 CVEs + 1 secret in same query → 3 evidence items with correct types."""
        collector = EvidenceCollector()
        fetcher = self._make_fetcher({
            "evidence_security": [
                {"finding_type": "cve", "location": "pkg.json", "finding_id": "CVE-1", "severity": "CRITICAL", "description": "vuln1", "package_name": "pkg1", "installed_version": "1.0", "fixed_version": "1.1", "tool_run_pk": 1},
                {"finding_type": "cve", "location": "pkg.json", "finding_id": "CVE-2", "severity": "HIGH", "description": "vuln2", "package_name": "pkg2", "installed_version": "2.0", "fixed_version": "2.1", "tool_run_pk": 1},
                {"finding_type": "secret", "location": "config.py", "finding_id": "api-key", "severity": "CRITICAL", "description": "API Key", "package_name": None, "installed_version": None, "fixed_version": None, "tool_run_pk": 1},
            ],
        })
        items = collector.collect(fetcher, run_pk=1)
        sec_items = [i for i in items if i.category == "security"]
        assert len(sec_items) == 3
        types = [i.evidence_type for i in sec_items]
        assert types.count("vulnerability") == 2
        assert types.count("secret_detection") == 1
        # Sequential IDs
        assert sec_items[0].evidence_id == "E-SEC-001"
        assert sec_items[1].evidence_id == "E-SEC-002"
        assert sec_items[2].evidence_id == "E-SEC-003"

    def test_collect_all_categories(self):
        """Verify all 6 categories are attempted."""
        collector = EvidenceCollector()
        fetcher = self._make_fetcher({
            "evidence_complexity": [{"relative_path": "a.py", "loc_total": 100, "complexity_max": 20, "total_ccn": 20, "function_count": 2, "avg_ccn": 10.0, "tool_run_pk": 1}],
            "evidence_security": [{"finding_type": "cve", "location": "b.py", "finding_id": "CVE-1", "severity": "HIGH", "description": "vuln", "package_name": "pkg", "installed_version": "1", "fixed_version": "2", "tool_run_pk": 1}],
            "evidence_coupling": [{"symbol_name": "X", "symbol_type": "class", "relative_path": "c.py", "fan_in": 1, "fan_out": 10, "total_coupling": 11, "instability": 0.9, "coupling_risk": "high", "coupling_pattern": "hub", "tool_run_pk": 1}],
            "evidence_coverage": [{"relative_path": "d.py", "loc_total": 200, "complexity_max": 20, "total_ccn": 20, "function_count": 3, "coverage_line_pct": 20, "branch_coverage_pct": 10, "tool_run_pk": 1}],
            "evidence_ownership": [{"relative_path": "e.py", "unique_authors": 1, "top_author": "dev", "top_author_pct": 100, "total_lines": 600, "risk_level": "critical", "tool_run_pk": 1}],
            "evidence_quality": [{"relative_path": "f.py", "loc_total": 200, "semgrep_smell_count": 10, "devskim_issue_count": 5, "smell_density_per_kloc": 50, "issue_density_per_kloc": 25, "tool_run_pk": 1}],
        })
        items = collector.collect(fetcher, run_pk=1)
        categories = {i.category for i in items}
        assert categories == {"complexity", "security", "coupling", "coverage", "ownership", "quality"}
