select
    run_pk,
    file_id,
    directory_id,
    relative_path,
    rule_id,
    secret_type,
    severity,
    line_number,
    commit_hash,
    commit_author,
    commit_date,
    fingerprint,
    in_current_head,
    entropy,
    description,
    created_at
from {{ source('lz', 'lz_gitleaks_secrets') }}
