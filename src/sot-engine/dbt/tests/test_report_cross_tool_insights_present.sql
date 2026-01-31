-- Fail if a collection run has both lizard and semgrep outputs but cross-tool joins are empty.
with run_summary as (
    select run_pk, collection_run_id
    from {{ ref('unified_run_summary') }}
),
tool_runs as (
    select run_pk, collection_run_id, tool_name
    from {{ source('lz', 'lz_tool_runs') }}
),
tool_map as (
    select
        rs.collection_run_id,
        max(case when tr.tool_name = 'lizard' then tr.run_pk end) as lizard_run_pk,
        max(case when tr.tool_name = 'semgrep' then tr.run_pk end) as semgrep_run_pk
    from run_summary rs
    left join tool_runs tr
        on tr.collection_run_id = rs.collection_run_id
    group by rs.collection_run_id
),
lizard_dir as (
    select run_pk, directory_path
    from {{ ref('rollup_lizard_directory_recursive_distributions') }}
    where metric = 'total_ccn'
),
semgrep_dir as (
    select run_pk, directory_path
    from {{ ref('rollup_semgrep_directory_recursive_distributions') }}
    where metric = 'smell_count'
),
joined as (
    select tm.collection_run_id
    from tool_map tm
    join lizard_dir l
        on l.run_pk = tm.lizard_run_pk
    join semgrep_dir s
        on s.run_pk = tm.semgrep_run_pk
        and s.directory_path = l.directory_path
)
select tm.collection_run_id
from tool_map tm
where tm.lizard_run_pk is not null
  and tm.semgrep_run_pk is not null
  and exists (
      select 1
      from lizard_dir l
      where l.run_pk = tm.lizard_run_pk
  )
  and exists (
      select 1
      from semgrep_dir s
      where s.run_pk = tm.semgrep_run_pk
  )
  and tm.collection_run_id not in (select collection_run_id from joined)
