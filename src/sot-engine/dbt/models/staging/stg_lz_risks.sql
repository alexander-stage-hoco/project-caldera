select
    collection_run_id,
    risk_id,
    description,
    technical_cause,
    claim_ids,
    manifests_in,
    triggered_by,
    severity,
    created_at
from {{ source('lz', 'lz_risks') }}
