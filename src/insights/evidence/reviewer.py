"""Evidence reviewer — human review workflow with state machine.

Manages the lifecycle of evidence sets through the review process:
``open`` → ``in_review`` → ``closed`` → ``accepted``.

When ``require_review=False`` (default), sets auto-transition from
``open`` directly to ``accepted`` for backward compatibility.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .entities import (
    EvidenceReview,
    EvidenceSetMetadata,
    EvidenceSetStatus,
    ParameterSet,
    ReviewVerdict,
)
from .param_persistence import load_parameter_set_from_db

# Valid status transitions
_TRANSITIONS: dict[EvidenceSetStatus, tuple[EvidenceSetStatus, ...]] = {
    "open": ("in_review", "accepted"),  # accepted for auto-accept path
    "in_review": ("closed",),
    "closed": ("accepted",),
    "accepted": (),  # terminal
}


class EvidenceReviewer:
    """Manages evidence set review workflow against DuckDB."""

    def __init__(self, conn: Any) -> None:
        self._conn = conn

    def get_set(self, evidence_set_id: str) -> EvidenceSetMetadata | None:
        """Load evidence set metadata by ID."""
        rows = self._conn.execute(
            "SELECT * FROM lz_evidence_sets WHERE evidence_set_id = ?",
            [evidence_set_id],
        ).fetchall()
        if not rows:
            return None
        cols = [d[0] for d in self._conn.execute(
            "SELECT * FROM lz_evidence_sets LIMIT 0"
        ).description]
        row = dict(zip(cols, rows[0]))
        return EvidenceSetMetadata(
            evidence_set_id=row["evidence_set_id"],
            collection_run_id=row["collection_run_id"],
            parameter_set_name=row["parameter_set_name"],
            status=row["status"],
            created_at=str(row["created_at"]),
            closed_at=str(row["closed_at"]) if row.get("closed_at") else None,
            total_items=row.get("total_items", 0),
            reviewed_items=row.get("reviewed_items", 0),
            accepted_items=row.get("accepted_items", 0),
            rejected_items=row.get("rejected_items", 0),
        )

    def get_parameters(self, evidence_set_id: str) -> ParameterSet | None:
        """Load structured parameters for an evidence set."""
        return load_parameter_set_from_db(self._conn, evidence_set_id)

    def list_sets(
        self,
        collection_run_id: str | None = None,
    ) -> list[EvidenceSetMetadata]:
        """List evidence sets, optionally filtered by collection run."""
        if collection_run_id:
            sql = (
                "SELECT * FROM lz_evidence_sets "
                "WHERE collection_run_id = ? ORDER BY created_at DESC"
            )
            rows = self._conn.execute(sql, [collection_run_id]).fetchall()
        else:
            sql = "SELECT * FROM lz_evidence_sets ORDER BY created_at DESC"
            rows = self._conn.execute(sql).fetchall()

        cols = [d[0] for d in self._conn.execute(
            "SELECT * FROM lz_evidence_sets LIMIT 0"
        ).description]
        return [
            EvidenceSetMetadata(
                evidence_set_id=r["evidence_set_id"],
                collection_run_id=r["collection_run_id"],
                parameter_set_name=r["parameter_set_name"],
                status=r["status"],
                created_at=str(r["created_at"]),
                closed_at=str(r["closed_at"]) if r.get("closed_at") else None,
                total_items=r.get("total_items", 0),
                reviewed_items=r.get("reviewed_items", 0),
                accepted_items=r.get("accepted_items", 0),
                rejected_items=r.get("rejected_items", 0),
            )
            for r in [dict(zip(cols, row)) for row in rows]
        ]

    def transition_status(
        self,
        evidence_set_id: str,
        new_status: EvidenceSetStatus,
    ) -> None:
        """Transition an evidence set to a new status."""
        current = self.get_set(evidence_set_id)
        if current is None:
            raise ValueError(f"Evidence set not found: {evidence_set_id}")

        valid_next = _TRANSITIONS.get(current.status, ())
        if new_status not in valid_next:
            raise ValueError(
                f"Cannot transition from {current.status!r} to {new_status!r}. "
                f"Valid transitions: {valid_next}"
            )

        updates = {"status": new_status}
        if new_status == "closed":
            updates["closed_at"] = datetime.now(timezone.utc).isoformat()

        set_clauses = ", ".join(f"{k} = ?" for k in updates)
        params = list(updates.values()) + [evidence_set_id]
        self._conn.execute(
            f"UPDATE lz_evidence_sets SET {set_clauses} WHERE evidence_set_id = ?",
            params,
        )

    def submit_review(
        self,
        evidence_set_id: str,
        evidence_id: str,
        verdict: ReviewVerdict,
        reviewer: str,
        notes: str | None = None,
        enhanced_observation: str | None = None,
        enhanced_why_it_matters: str | None = None,
    ) -> None:
        """Submit a review verdict for a single evidence item."""
        now = datetime.now(timezone.utc).isoformat()

        # Upsert the review
        self._conn.execute(
            """
            INSERT INTO lz_evidence_reviews (
                evidence_set_id, evidence_id, verdict, reviewer,
                reviewed_at, notes, enhanced_observation, enhanced_why_it_matters
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (evidence_set_id, evidence_id) DO UPDATE SET
                verdict = EXCLUDED.verdict,
                reviewer = EXCLUDED.reviewer,
                reviewed_at = EXCLUDED.reviewed_at,
                notes = EXCLUDED.notes,
                enhanced_observation = EXCLUDED.enhanced_observation,
                enhanced_why_it_matters = EXCLUDED.enhanced_why_it_matters
            """,
            [
                evidence_set_id, evidence_id, verdict, reviewer,
                now, notes, enhanced_observation, enhanced_why_it_matters,
            ],
        )

        # Update counts on the evidence set
        self._update_review_counts(evidence_set_id)

    def get_pending(self, evidence_set_id: str) -> list[str]:
        """Get evidence IDs with pending or no review."""
        rows = self._conn.execute(
            """
            SELECT e.evidence_id
            FROM lz_evidence e
            LEFT JOIN lz_evidence_reviews r
                ON r.evidence_set_id = e.evidence_set_id
                AND r.evidence_id = e.evidence_id
            WHERE e.evidence_set_id = ?
              AND (r.verdict IS NULL OR r.verdict = 'pending')
            """,
            [evidence_set_id],
        ).fetchall()
        return [row[0] for row in rows]

    def get_reviews(self, evidence_set_id: str) -> list[EvidenceReview]:
        """Get all reviews for an evidence set."""
        rows = self._conn.execute(
            "SELECT * FROM lz_evidence_reviews WHERE evidence_set_id = ?",
            [evidence_set_id],
        ).fetchall()
        cols = [d[0] for d in self._conn.execute(
            "SELECT * FROM lz_evidence_reviews LIMIT 0"
        ).description]
        return [
            EvidenceReview(
                evidence_id=r["evidence_id"],
                verdict=r["verdict"],
                reviewer=r.get("reviewer", ""),
                reviewed_at=str(r["reviewed_at"]) if r.get("reviewed_at") else "",
                notes=r.get("notes"),
                enhanced_observation=r.get("enhanced_observation"),
                enhanced_why_it_matters=r.get("enhanced_why_it_matters"),
            )
            for r in [dict(zip(cols, row)) for row in rows]
        ]

    def is_fully_reviewed(self, evidence_set_id: str) -> bool:
        """Check if all evidence items have been reviewed (not pending)."""
        pending = self.get_pending(evidence_set_id)
        return len(pending) == 0

    def batch_accept(self, evidence_set_id: str, reviewer: str) -> int:
        """Accept all pending evidence items in a set. Returns count."""
        pending = self.get_pending(evidence_set_id)
        for eid in pending:
            self.submit_review(evidence_set_id, eid, "accepted", reviewer)
        return len(pending)

    def _update_review_counts(self, evidence_set_id: str) -> None:
        """Refresh review counts on the evidence set."""
        row = self._conn.execute(
            """
            SELECT
                COUNT(*) FILTER (WHERE verdict != 'pending') AS reviewed,
                COUNT(*) FILTER (WHERE verdict = 'accepted' OR verdict = 'enhanced') AS accepted,
                COUNT(*) FILTER (WHERE verdict = 'rejected') AS rejected
            FROM lz_evidence_reviews
            WHERE evidence_set_id = ?
            """,
            [evidence_set_id],
        ).fetchone()
        if row:
            self._conn.execute(
                """
                UPDATE lz_evidence_sets
                SET reviewed_items = ?, accepted_items = ?, rejected_items = ?
                WHERE evidence_set_id = ?
                """,
                [row[0], row[1], row[2], evidence_set_id],
            )
