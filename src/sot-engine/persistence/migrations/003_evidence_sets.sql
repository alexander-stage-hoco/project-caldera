-- Migration 003: Add evidence sets, reviews, and metadata support
-- Adds multi-set, parameterized, human-reviewable evidence system

-- Add metadata_json column to lz_evidence
ALTER TABLE lz_evidence ADD COLUMN IF NOT EXISTS metadata_json TEXT;

-- Add evidence_set_id columns to existing tables
ALTER TABLE lz_evidence ADD COLUMN IF NOT EXISTS evidence_set_id VARCHAR;
ALTER TABLE lz_claims ADD COLUMN IF NOT EXISTS evidence_set_id VARCHAR;
ALTER TABLE lz_risks ADD COLUMN IF NOT EXISTS evidence_set_id VARCHAR;

-- Evidence set metadata table
CREATE TABLE IF NOT EXISTS lz_evidence_sets (
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

-- Evidence review table
CREATE TABLE IF NOT EXISTS lz_evidence_reviews (
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

-- Backfill existing evidence data with synthetic evidence_set_id
-- Format: <collection_run_id>-default
UPDATE lz_evidence
SET evidence_set_id = collection_run_id || '-default'
WHERE evidence_set_id IS NULL;

UPDATE lz_claims
SET evidence_set_id = collection_run_id || '-default'
WHERE evidence_set_id IS NULL;

UPDATE lz_risks
SET evidence_set_id = collection_run_id || '-default'
WHERE evidence_set_id IS NULL;

-- Create synthetic evidence set records for existing data
INSERT INTO lz_evidence_sets (
    evidence_set_id, collection_run_id, parameter_set_name,
    parameter_set_json, status, total_items, accepted_items
)
SELECT DISTINCT
    e.evidence_set_id,
    e.collection_run_id,
    'default',
    '{}',
    'accepted',
    COUNT(*) OVER (PARTITION BY e.evidence_set_id),
    COUNT(*) OVER (PARTITION BY e.evidence_set_id)
FROM lz_evidence e
WHERE e.evidence_set_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM lz_evidence_sets es
    WHERE es.evidence_set_id = e.evidence_set_id
  )
GROUP BY e.evidence_set_id, e.collection_run_id;
