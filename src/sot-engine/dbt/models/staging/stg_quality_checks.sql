select
    collection_run_id,
    tool_name,
    check_name,
    level,
    passed,
    severity,
    message,
    overall_score,
    created_at
from {{ source('lz', 'lz_quality_checks') }}
