"""Tests for EvidenceReviewer with in-memory DuckDB."""

from __future__ import annotations

import duckdb
import pytest

from insights.evidence.reviewer import EvidenceReviewer

_SCHEMA = """
CREATE TABLE lz_evidence_sets (
    evidence_set_id VARCHAR NOT NULL,
    collection_run_id VARCHAR NOT NULL,
    parameter_set_name VARCHAR NOT NULL,
    parameter_set_json TEXT NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    total_items INTEGER DEFAULT 0,
    reviewed_items INTEGER DEFAULT 0,
    accepted_items INTEGER DEFAULT 0,
    rejected_items INTEGER DEFAULT 0,
    PRIMARY KEY (evidence_set_id)
);

CREATE TABLE lz_evidence (
    collection_run_id VARCHAR NOT NULL,
    evidence_id VARCHAR NOT NULL,
    evidence_type VARCHAR NOT NULL,
    category VARCHAR NOT NULL,
    location VARCHAR NOT NULL,
    excerpt TEXT,
    observation TEXT,
    why_it_matters TEXT,
    tool_source VARCHAR NOT NULL,
    run_pk BIGINT NOT NULL,
    confidence VARCHAR NOT NULL DEFAULT 'high',
    metadata_json TEXT,
    evidence_set_id VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (collection_run_id, evidence_id)
);

CREATE TABLE lz_evidence_reviews (
    evidence_set_id VARCHAR NOT NULL,
    evidence_id VARCHAR NOT NULL,
    verdict VARCHAR NOT NULL DEFAULT 'pending',
    reviewer VARCHAR,
    reviewed_at TIMESTAMP,
    notes TEXT,
    enhanced_observation TEXT,
    enhanced_why_it_matters TEXT,
    PRIMARY KEY (evidence_set_id, evidence_id)
);
"""


def _make_conn() -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(":memory:")
    conn.execute(_SCHEMA)
    return conn


def _seed(conn: duckdb.DuckDBPyConnection) -> str:
    """Seed an evidence set with 3 items, return evidence_set_id."""
    set_id = "set-001"
    crun_id = "run-001"

    conn.execute(
        "INSERT INTO lz_evidence_sets "
        "(evidence_set_id, collection_run_id, parameter_set_name, parameter_set_json, status, total_items) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [set_id, crun_id, "default", "{}", "open", 3],
    )

    for i in range(1, 4):
        conn.execute(
            "INSERT INTO lz_evidence "
            "(collection_run_id, evidence_id, evidence_type, category, location, "
            "excerpt, observation, why_it_matters, tool_source, run_pk, evidence_set_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [crun_id, f"E-CCN-{i:03d}", "test", "complexity", "src/file.py",
             "test", "test", "test", "lizard", 1, set_id],
        )
        conn.execute(
            "INSERT INTO lz_evidence_reviews "
            "(evidence_set_id, evidence_id, verdict) VALUES (?, ?, ?)",
            [set_id, f"E-CCN-{i:03d}", "pending"],
        )

    return set_id


class TestEvidenceReviewer:
    def test_get_set(self):
        conn = _make_conn()
        set_id = _seed(conn)
        reviewer = EvidenceReviewer(conn)
        es = reviewer.get_set(set_id)
        assert es is not None
        assert es.evidence_set_id == set_id
        assert es.status == "open"
        assert es.total_items == 3

    def test_get_set_not_found(self):
        conn = _make_conn()
        reviewer = EvidenceReviewer(conn)
        assert reviewer.get_set("nonexistent") is None

    def test_list_sets(self):
        conn = _make_conn()
        _seed(conn)
        reviewer = EvidenceReviewer(conn)
        sets = reviewer.list_sets()
        assert len(sets) == 1

    def test_list_sets_filtered(self):
        conn = _make_conn()
        _seed(conn)
        reviewer = EvidenceReviewer(conn)
        sets = reviewer.list_sets(collection_run_id="run-001")
        assert len(sets) == 1
        sets = reviewer.list_sets(collection_run_id="nonexistent")
        assert len(sets) == 0

    def test_transition_open_to_in_review(self):
        conn = _make_conn()
        set_id = _seed(conn)
        reviewer = EvidenceReviewer(conn)
        reviewer.transition_status(set_id, "in_review")
        es = reviewer.get_set(set_id)
        assert es.status == "in_review"

    def test_transition_open_to_accepted(self):
        """Auto-accept path: open → accepted."""
        conn = _make_conn()
        set_id = _seed(conn)
        reviewer = EvidenceReviewer(conn)
        reviewer.transition_status(set_id, "accepted")
        es = reviewer.get_set(set_id)
        assert es.status == "accepted"

    def test_invalid_transition_raises(self):
        conn = _make_conn()
        set_id = _seed(conn)
        reviewer = EvidenceReviewer(conn)
        with pytest.raises(ValueError, match="Cannot transition"):
            reviewer.transition_status(set_id, "closed")

    def test_submit_review(self):
        conn = _make_conn()
        set_id = _seed(conn)
        reviewer = EvidenceReviewer(conn)
        reviewer.submit_review(set_id, "E-CCN-001", "accepted", "alice")
        reviews = reviewer.get_reviews(set_id)
        accepted = [r for r in reviews if r.verdict == "accepted"]
        assert len(accepted) == 1
        assert accepted[0].reviewer == "alice"

    def test_submit_review_updates_counts(self):
        conn = _make_conn()
        set_id = _seed(conn)
        reviewer = EvidenceReviewer(conn)
        reviewer.submit_review(set_id, "E-CCN-001", "accepted", "alice")
        reviewer.submit_review(set_id, "E-CCN-002", "rejected", "alice")
        es = reviewer.get_set(set_id)
        assert es.reviewed_items == 2
        assert es.accepted_items == 1
        assert es.rejected_items == 1

    def test_get_pending(self):
        conn = _make_conn()
        set_id = _seed(conn)
        reviewer = EvidenceReviewer(conn)
        pending = reviewer.get_pending(set_id)
        assert len(pending) == 3

        reviewer.submit_review(set_id, "E-CCN-001", "accepted", "alice")
        pending = reviewer.get_pending(set_id)
        assert len(pending) == 2
        assert "E-CCN-001" not in pending

    def test_is_fully_reviewed(self):
        conn = _make_conn()
        set_id = _seed(conn)
        reviewer = EvidenceReviewer(conn)
        assert reviewer.is_fully_reviewed(set_id) is False

        for i in range(1, 4):
            reviewer.submit_review(set_id, f"E-CCN-{i:03d}", "accepted", "alice")
        assert reviewer.is_fully_reviewed(set_id) is True

    def test_batch_accept(self):
        conn = _make_conn()
        set_id = _seed(conn)
        reviewer = EvidenceReviewer(conn)
        count = reviewer.batch_accept(set_id, "bot")
        assert count == 3
        assert reviewer.is_fully_reviewed(set_id) is True
        es = reviewer.get_set(set_id)
        assert es.accepted_items == 3

    def test_full_lifecycle(self):
        """open → in_review → (review all) → closed → accepted."""
        conn = _make_conn()
        set_id = _seed(conn)
        reviewer = EvidenceReviewer(conn)

        reviewer.transition_status(set_id, "in_review")
        for i in range(1, 4):
            reviewer.submit_review(set_id, f"E-CCN-{i:03d}", "accepted", "alice")
        reviewer.transition_status(set_id, "closed")
        reviewer.transition_status(set_id, "accepted")

        es = reviewer.get_set(set_id)
        assert es.status == "accepted"
        assert es.accepted_items == 3

    def test_enhanced_review(self):
        conn = _make_conn()
        set_id = _seed(conn)
        reviewer = EvidenceReviewer(conn)
        reviewer.submit_review(
            set_id, "E-CCN-001", "enhanced", "alice",
            notes="Confirmed after manual inspection",
            enhanced_observation="Actually CCN is 30, not 25",
            enhanced_why_it_matters="Critical hot path",
        )
        reviews = reviewer.get_reviews(set_id)
        enhanced = [r for r in reviews if r.verdict == "enhanced"]
        assert len(enhanced) == 1
        assert enhanced[0].enhanced_observation == "Actually CCN is 30, not 25"
