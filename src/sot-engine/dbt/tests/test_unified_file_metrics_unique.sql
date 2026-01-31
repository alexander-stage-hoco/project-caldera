select
    run_pk,
    file_id,
    count(*) as row_count
from {{ ref('unified_file_metrics') }}
group by run_pk, file_id
having count(*) > 1
