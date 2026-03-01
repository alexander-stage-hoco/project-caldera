select
    collection_run_id,
    evidence_id,
    evidence_type,
    category,
    location,
    excerpt,
    observation,
    why_it_matters,
    tool_source,
    run_pk,
    confidence,
    created_at
from {{ source('lz', 'lz_evidence') }}
