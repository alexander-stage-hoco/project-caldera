-- Migration 004: Structured evidence parameter storage
--
-- Adds typed, relational child tables of lz_evidence_sets for query, claim,
-- and risk parameters.  The JSON blob (parameter_set_json) is kept for
-- backward compatibility but the structured tables are the system of record.

CREATE TABLE IF NOT EXISTS lz_evidence_query_params (
    evidence_set_id    VARCHAR NOT NULL,
    query_name         VARCHAR NOT NULL,
    threshold          INTEGER,
    limit_rows         INTEGER,
    coverage_threshold INTEGER,
    ccn_threshold      INTEGER,
    density_threshold  INTEGER,
    loc_threshold      INTEGER,
    min_files          INTEGER,
    min_depth          INTEGER,
    gini_threshold     DOUBLE,
    pct_threshold      INTEGER,
    PRIMARY KEY (evidence_set_id, query_name),
    FOREIGN KEY (evidence_set_id) REFERENCES lz_evidence_sets(evidence_set_id)
);

CREATE TABLE IF NOT EXISTS lz_evidence_claim_params (
    evidence_set_id    VARCHAR NOT NULL,
    rule_name          VARCHAR NOT NULL,
    fan_out_multiplier INTEGER,
    min_fan_out        INTEGER,
    max_authors        INTEGER,
    min_lines          INTEGER,
    max_coverage       INTEGER,
    min_ccn            INTEGER,
    min_categories     INTEGER,
    PRIMARY KEY (evidence_set_id, rule_name),
    FOREIGN KEY (evidence_set_id) REFERENCES lz_evidence_sets(evidence_set_id)
);

CREATE TABLE IF NOT EXISTS lz_evidence_risk_params (
    evidence_set_id  VARCHAR NOT NULL,
    pattern_name     VARCHAR NOT NULL,
    min_claims       INTEGER,
    default_severity VARCHAR,
    PRIMARY KEY (evidence_set_id, pattern_name),
    FOREIGN KEY (evidence_set_id) REFERENCES lz_evidence_sets(evidence_set_id)
);
