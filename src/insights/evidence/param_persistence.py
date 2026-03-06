"""Conversion + DB read/write for structured evidence parameter storage.

Maps between ``ParameterSet`` (in-memory, YAML-derived) and typed DB records
in ``lz_evidence_query_params``, ``lz_evidence_claim_params``, and
``lz_evidence_risk_params``.
"""

from __future__ import annotations

from typing import Any

from .entities import (
    ClaimParamRecord,
    ParameterSet,
    QueryParamRecord,
    RiskParamRecord,
)

# ---------------------------------------------------------------------------
# Column mapping constants — single source of truth for YAML-key <-> DB-column
# ---------------------------------------------------------------------------

_QUERY_COLUMN_MAP: dict[str, dict[str, str]] = {
    "evidence_complexity": {"threshold": "threshold", "limit": "limit_rows"},
    "evidence_security": {"limit": "limit_rows"},
    "evidence_coupling": {"limit": "limit_rows"},
    "evidence_coverage": {"coverage_threshold": "coverage_threshold", "ccn_threshold": "ccn_threshold", "limit": "limit_rows"},
    "evidence_ownership": {"limit": "limit_rows"},
    "evidence_quality": {"density_threshold": "density_threshold", "limit": "limit_rows"},
    "evidence_maintainability": {"loc_threshold": "loc_threshold", "limit": "limit_rows"},
    "evidence_architecture": {"min_files": "min_files", "min_depth": "min_depth", "limit": "limit_rows"},
    "evidence_dependencies": {"limit": "limit_rows"},
    "evidence_duplication": {"limit": "limit_rows"},
    "claim_complexity_concentration": {"gini_threshold": "gini_threshold", "min_files": "min_files"},
    "claim_pervasive_smells": {"pct_threshold": "pct_threshold"},
}

_CLAIM_COLUMN_MAP: dict[str, dict[str, str]] = {
    "HighCouplingRule": {"fan_out_multiplier": "fan_out_multiplier", "min_fan_out": "min_fan_out"},
    "KnowledgeSiloRule": {"max_authors": "max_authors", "min_lines": "min_lines"},
    "CoverageGapRule": {"max_coverage": "max_coverage", "min_ccn": "min_ccn"},
    "LLMSynthesisRule": {"min_categories": "min_categories"},
}

_RISK_COLUMN_MAP: dict[str, str] = {
    "min_claims": "min_claims",
    "default_severity": "default_severity",
}

# All typed columns on QueryParamRecord (excluding evidence_set_id, query_name)
_QUERY_DB_COLUMNS = (
    "threshold", "limit_rows", "coverage_threshold", "ccn_threshold",
    "density_threshold", "loc_threshold", "min_files", "min_depth",
    "gini_threshold", "pct_threshold",
)

_CLAIM_DB_COLUMNS = (
    "fan_out_multiplier", "min_fan_out", "max_authors", "min_lines",
    "max_coverage", "min_ccn", "min_categories",
)

_RISK_DB_COLUMNS = ("min_claims", "default_severity")


# ---------------------------------------------------------------------------
# ParameterSet -> typed records
# ---------------------------------------------------------------------------


def parameter_set_to_records(
    ps: ParameterSet,
    evidence_set_id: str,
) -> tuple[list[QueryParamRecord], list[ClaimParamRecord], list[RiskParamRecord]]:
    """Convert an in-memory ParameterSet to typed DB records."""
    query_records: list[QueryParamRecord] = []
    for query_name, params in ps.query_params.items():
        col_map = _QUERY_COLUMN_MAP.get(query_name, {})
        kwargs: dict[str, Any] = {}
        for yaml_key, db_col in col_map.items():
            if yaml_key in params:
                kwargs[db_col] = params[yaml_key]
        query_records.append(
            QueryParamRecord(
                evidence_set_id=evidence_set_id,
                query_name=query_name,
                **kwargs,
            )
        )

    claim_records: list[ClaimParamRecord] = []
    for rule_name, params in ps.claim_params.items():
        col_map = _CLAIM_COLUMN_MAP.get(rule_name, {})
        kwargs = {}
        for yaml_key, db_col in col_map.items():
            if yaml_key in params:
                kwargs[db_col] = params[yaml_key]
        claim_records.append(
            ClaimParamRecord(
                evidence_set_id=evidence_set_id,
                rule_name=rule_name,
                **kwargs,
            )
        )

    risk_records: list[RiskParamRecord] = []
    for pattern_name, params in ps.risk_params.items():
        kwargs = {}
        for yaml_key, db_col in _RISK_COLUMN_MAP.items():
            if yaml_key in params:
                kwargs[db_col] = params[yaml_key]
        risk_records.append(
            RiskParamRecord(
                evidence_set_id=evidence_set_id,
                pattern_name=pattern_name,
                **kwargs,
            )
        )

    return query_records, claim_records, risk_records


# ---------------------------------------------------------------------------
# DB persistence
# ---------------------------------------------------------------------------


def persist_params(
    conn: Any,
    evidence_set_id: str,
    query_records: list[QueryParamRecord],
    claim_records: list[ClaimParamRecord],
    risk_records: list[RiskParamRecord],
) -> None:
    """Idempotent: DELETE + INSERT for the given evidence_set_id."""
    for table in (
        "lz_evidence_query_params",
        "lz_evidence_claim_params",
        "lz_evidence_risk_params",
    ):
        conn.execute(
            f"DELETE FROM {table} WHERE evidence_set_id = ?",
            [evidence_set_id],
        )

    if query_records:
        cols = ("evidence_set_id", "query_name") + _QUERY_DB_COLUMNS
        placeholders = ", ".join("?" for _ in cols)
        conn.executemany(
            f"INSERT INTO lz_evidence_query_params ({', '.join(cols)}) VALUES ({placeholders})",
            [
                (
                    r.evidence_set_id, r.query_name,
                    r.threshold, r.limit_rows, r.coverage_threshold,
                    r.ccn_threshold, r.density_threshold, r.loc_threshold,
                    r.min_files, r.min_depth, r.gini_threshold, r.pct_threshold,
                )
                for r in query_records
            ],
        )

    if claim_records:
        cols = ("evidence_set_id", "rule_name") + _CLAIM_DB_COLUMNS
        placeholders = ", ".join("?" for _ in cols)
        conn.executemany(
            f"INSERT INTO lz_evidence_claim_params ({', '.join(cols)}) VALUES ({placeholders})",
            [
                (
                    r.evidence_set_id, r.rule_name,
                    r.fan_out_multiplier, r.min_fan_out, r.max_authors,
                    r.min_lines, r.max_coverage, r.min_ccn, r.min_categories,
                )
                for r in claim_records
            ],
        )

    if risk_records:
        cols = ("evidence_set_id", "pattern_name") + _RISK_DB_COLUMNS
        placeholders = ", ".join("?" for _ in cols)
        conn.executemany(
            f"INSERT INTO lz_evidence_risk_params ({', '.join(cols)}) VALUES ({placeholders})",
            [
                (r.evidence_set_id, r.pattern_name, r.min_claims, r.default_severity)
                for r in risk_records
            ],
        )


# ---------------------------------------------------------------------------
# DB -> ParameterSet reconstruction
# ---------------------------------------------------------------------------


def _invert_map(col_map: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    """Invert {query_name: {yaml_key: db_col}} -> {query_name: {db_col: yaml_key}}."""
    return {
        name: {db_col: yaml_key for yaml_key, db_col in mapping.items()}
        for name, mapping in col_map.items()
    }


_INV_QUERY_MAP = _invert_map(_QUERY_COLUMN_MAP)
_INV_CLAIM_MAP = _invert_map(_CLAIM_COLUMN_MAP)
_INV_RISK_MAP = {db_col: yaml_key for yaml_key, db_col in _RISK_COLUMN_MAP.items()}


def load_parameter_set_from_db(
    conn: Any,
    evidence_set_id: str,
) -> ParameterSet | None:
    """Reconstruct a ParameterSet from the structured param tables.

    Returns ``None`` if no rows exist for *evidence_set_id*.
    NULL columns are skipped so application defaults apply.
    """
    # Load the parameter set name from the parent table
    row = conn.execute(
        "SELECT parameter_set_name FROM lz_evidence_sets WHERE evidence_set_id = ?",
        [evidence_set_id],
    ).fetchone()
    if row is None:
        return None
    ps_name = row[0]

    # Query params
    query_params: dict[str, dict[str, Any]] = {}
    q_rows = conn.execute(
        "SELECT * FROM lz_evidence_query_params WHERE evidence_set_id = ?",
        [evidence_set_id],
    ).fetchall()
    if q_rows:
        q_cols = [d[0] for d in conn.execute(
            "SELECT * FROM lz_evidence_query_params LIMIT 0"
        ).description]
        for qr in q_rows:
            rd = dict(zip(q_cols, qr))
            qname = rd["query_name"]
            inv = _INV_QUERY_MAP.get(qname, {})
            params: dict[str, Any] = {}
            for db_col in _QUERY_DB_COLUMNS:
                val = rd.get(db_col)
                if val is not None:
                    yaml_key = inv.get(db_col, db_col)
                    params[yaml_key] = val
            query_params[qname] = params

    # Claim params
    claim_params: dict[str, dict[str, Any]] = {}
    c_rows = conn.execute(
        "SELECT * FROM lz_evidence_claim_params WHERE evidence_set_id = ?",
        [evidence_set_id],
    ).fetchall()
    if c_rows:
        c_cols = [d[0] for d in conn.execute(
            "SELECT * FROM lz_evidence_claim_params LIMIT 0"
        ).description]
        for cr in c_rows:
            rd = dict(zip(c_cols, cr))
            rname = rd["rule_name"]
            inv = _INV_CLAIM_MAP.get(rname, {})
            params = {}
            for db_col in _CLAIM_DB_COLUMNS:
                val = rd.get(db_col)
                if val is not None:
                    yaml_key = inv.get(db_col, db_col)
                    params[yaml_key] = val
            claim_params[rname] = params

    # Risk params
    risk_params: dict[str, dict[str, Any]] = {}
    r_rows = conn.execute(
        "SELECT * FROM lz_evidence_risk_params WHERE evidence_set_id = ?",
        [evidence_set_id],
    ).fetchall()
    if r_rows:
        r_cols = [d[0] for d in conn.execute(
            "SELECT * FROM lz_evidence_risk_params LIMIT 0"
        ).description]
        for rr in r_rows:
            rd = dict(zip(r_cols, rr))
            pname = rd["pattern_name"]
            params = {}
            for db_col in _RISK_DB_COLUMNS:
                val = rd.get(db_col)
                if val is not None:
                    yaml_key = _INV_RISK_MAP.get(db_col, db_col)
                    params[yaml_key] = val
            risk_params[pname] = params

    has_data = bool(query_params or claim_params or risk_params)
    if not has_data:
        return None

    return ParameterSet(
        name=ps_name,
        description="",
        query_params=query_params,
        claim_params=claim_params,
        risk_params=risk_params,
        action_params={},
    )
