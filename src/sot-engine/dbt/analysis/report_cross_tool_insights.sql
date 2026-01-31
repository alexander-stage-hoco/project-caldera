{% set run_pk = var('run_pk') %}
{% set limit_rows = var('limit', 10) %}

with run_summary as (
    select run_pk, collection_run_id
    from {{ ref('unified_run_summary') }}
    where run_pk = {{ run_pk }}
),
tool_runs as (
    select run_pk, collection_run_id, tool_name
    from {{ source('lz', 'lz_tool_runs') }}
),
tool_map as (
    select
        rs.collection_run_id,
        max(case when tr.tool_name = 'scc' then tr.run_pk end) as scc_run_pk,
        max(case when tr.tool_name = 'lizard' then tr.run_pk end) as lizard_run_pk,
        max(case when tr.tool_name = 'semgrep' then tr.run_pk end) as semgrep_run_pk,
        max(case when tr.tool_name in ('roslyn', 'roslyn-analyzers') then tr.run_pk end) as roslyn_run_pk
    from run_summary rs
    left join tool_runs tr
        on tr.collection_run_id = rs.collection_run_id
    group by rs.collection_run_id
),
lizard_dir as (
    select *
    from {{ ref('rollup_lizard_directory_recursive_distributions') }}
    where run_pk = (select lizard_run_pk from tool_map)
      and metric = 'total_ccn'
),
semgrep_dir as (
    select *
    from {{ ref('rollup_semgrep_directory_recursive_distributions') }}
    where run_pk = (select semgrep_run_pk from tool_map)
      and metric = 'smell_count'
),
roslyn_dir as (
    select *
    from {{ ref('rollup_roslyn_directory_recursive_distributions') }}
    where run_pk = (select roslyn_run_pk from tool_map)
      and metric = 'violation_count'
),
scc_dir as (
    select *
    from {{ ref('rollup_scc_directory_recursive_distributions') }}
    where run_pk = (select scc_run_pk from tool_map)
      and metric = 'lines_total'
),
complexity_smells as (
    select
        'complexity_x_smells' as insight,
        l.directory_path,
        l.p95_value as ccn_p95,
        s.p95_value as smells_p95,
        l.gini_value as ccn_gini,
        s.gini_value as smells_gini,
        (l.p95_value * s.p95_value) as score,
        row_number() over (
            order by l.p95_value * s.p95_value desc, l.directory_path
        ) as rank_id
    from lizard_dir l
    join semgrep_dir s
        on s.directory_path = l.directory_path
),
complexity_roslyn as (
    select
        'complexity_x_roslyn' as insight,
        l.directory_path,
        l.p95_value as ccn_p95,
        r.p95_value as violations_p95,
        l.gini_value as ccn_gini,
        r.gini_value as violations_gini,
        (l.p95_value * r.p95_value) as score,
        row_number() over (
            order by l.p95_value * r.p95_value desc, l.directory_path
        ) as rank_id
    from lizard_dir l
    join roslyn_dir r
        on r.directory_path = l.directory_path
),
violation_density as (
    select
        'violations_per_kloc' as insight,
        r.directory_path,
        r.total_violation_count as violations,
        (s.avg_value * s.value_count) as loc_total,
        case
            when s.avg_value * s.value_count = 0 then 0
            else (r.total_violation_count / (s.avg_value * s.value_count)) * 1000
        end as violations_per_kloc,
        row_number() over (
            order by violations_per_kloc desc, r.directory_path
        ) as rank_id
    from {{ ref('rollup_roslyn_directory_counts_recursive') }} r
    join scc_dir s
        on s.directory_path = r.directory_path
    where r.run_pk = (select roslyn_run_pk from tool_map)
)
select
    insight,
    directory_path,
    ccn_p95,
    smells_p95,
    violations_p95,
    ccn_gini,
    smells_gini,
    violations_gini,
    score,
    violations,
    loc_total,
    violations_per_kloc,
    rank_id
from (
    select
        insight,
        directory_path,
        ccn_p95,
        smells_p95,
        cast(null as double) as violations_p95,
        ccn_gini,
        smells_gini,
        cast(null as double) as violations_gini,
        score,
        cast(null as double) as violations,
        cast(null as double) as loc_total,
        cast(null as double) as violations_per_kloc,
        rank_id
    from complexity_smells
    union all
    select
        insight,
        directory_path,
        ccn_p95,
        cast(null as double) as smells_p95,
        violations_p95,
        ccn_gini,
        cast(null as double) as smells_gini,
        violations_gini,
        score,
        cast(null as double) as violations,
        cast(null as double) as loc_total,
        cast(null as double) as violations_per_kloc,
        rank_id
    from complexity_roslyn
    union all
    select
        insight,
        directory_path,
        cast(null as double) as ccn_p95,
        cast(null as double) as smells_p95,
        cast(null as double) as violations_p95,
        cast(null as double) as ccn_gini,
        cast(null as double) as smells_gini,
        cast(null as double) as violations_gini,
        cast(null as double) as score,
        violations,
        loc_total,
        violations_per_kloc,
        rank_id
    from violation_density
)
where rank_id <= {{ limit_rows }}
order by insight, rank_id
