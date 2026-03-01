select
    collection_run_id,
    category,
    source,
    message,
    created_at
from {{ source('lz', 'lz_warnings') }}
