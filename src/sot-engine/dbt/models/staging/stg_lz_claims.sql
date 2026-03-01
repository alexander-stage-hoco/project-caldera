select
    collection_run_id,
    claim_id,
    category,
    statement,
    evidence_ids,
    implication,
    confidence,
    triggered_by,
    severity,
    created_at
from {{ source('lz', 'lz_claims') }}
