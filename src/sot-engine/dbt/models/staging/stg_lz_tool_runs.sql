select
    run_pk,
    collection_run_id,
    repo_id,
    run_id,
    tool_name,
    tool_version,
    schema_version,
    branch,
    commit,
    timestamp,
    created_at
from {{ source('lz', 'lz_tool_runs') }}
