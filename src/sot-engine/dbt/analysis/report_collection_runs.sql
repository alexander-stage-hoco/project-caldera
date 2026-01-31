select
    cr.collection_run_id,
    cr.repo_id,
    cr.run_id,
    cr.branch,
    cr.commit,
    cr.status,
    cr.started_at,
    cr.completed_at,
    count(tr.run_pk) as tool_runs
from {{ source('lz', 'lz_collection_runs') }} cr
left join {{ source('lz', 'lz_tool_runs') }} tr
    on tr.collection_run_id = cr.collection_run_id
group by
    cr.collection_run_id,
    cr.repo_id,
    cr.run_id,
    cr.branch,
    cr.commit,
    cr.status,
    cr.started_at,
    cr.completed_at
order by cr.started_at desc
