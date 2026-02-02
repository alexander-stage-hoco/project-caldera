{% set run_pk = var('run_pk') %}

-- Repository-level module health summary across all 5 tools
-- Aggregates health metrics for executive reporting

-- Resolve tool-specific run_pks from collection
with run_map as (
    select
        tr_anchor.run_pk as scc_run_pk,
        tr_lizard.run_pk as lizard_run_pk,
        tr_semgrep.run_pk as semgrep_run_pk,
        tr_roslyn.run_pk as roslyn_run_pk,
        tr_sonarqube.run_pk as sonarqube_run_pk
    from {{ source('lz', 'lz_tool_runs') }} tr_anchor
    left join {{ source('lz', 'lz_tool_runs') }} tr_lizard
        on tr_lizard.collection_run_id = tr_anchor.collection_run_id
        and tr_lizard.tool_name = 'lizard'
    left join {{ source('lz', 'lz_tool_runs') }} tr_semgrep
        on tr_semgrep.collection_run_id = tr_anchor.collection_run_id
        and tr_semgrep.tool_name = 'semgrep'
    left join {{ source('lz', 'lz_tool_runs') }} tr_roslyn
        on tr_roslyn.collection_run_id = tr_anchor.collection_run_id
        and tr_roslyn.tool_name in ('roslyn', 'roslyn-analyzers')
    left join {{ source('lz', 'lz_tool_runs') }} tr_sonarqube
        on tr_sonarqube.collection_run_id = tr_anchor.collection_run_id
        and tr_sonarqube.tool_name = 'sonarqube'
    where tr_anchor.tool_name = 'scc'
      and tr_anchor.run_pk = {{ run_pk }}
),
scc_summary as (
    select
        'scc' as tool,
        'lines_total' as metric,
        count(*) as directory_count,
        avg(gini_value) as avg_gini,
        max(gini_value) as max_gini,
        sum(case when gini_value >= 0.5 then 1 else 0 end) as high_inequality_dirs,
        sum(case when top_20_pct_share >= 0.7 then 1 else 0 end) as high_concentration_dirs
    from {{ ref('rollup_scc_directory_recursive_distributions') }}
    where run_pk = (select scc_run_pk from run_map)
      and metric = 'lines_total'
      and value_count >= 3
),
lizard_summary as (
    select
        'lizard' as tool,
        'total_ccn' as metric,
        count(*) as directory_count,
        avg(gini_value) as avg_gini,
        max(gini_value) as max_gini,
        sum(case when gini_value >= 0.5 then 1 else 0 end) as high_inequality_dirs,
        sum(case when top_20_pct_share >= 0.7 then 1 else 0 end) as high_concentration_dirs
    from {{ ref('rollup_lizard_directory_recursive_distributions') }}
    where run_pk = (select lizard_run_pk from run_map)
      and metric = 'total_ccn'
      and value_count >= 3
),
semgrep_summary as (
    select
        'semgrep' as tool,
        'smell_count' as metric,
        count(*) as directory_count,
        avg(gini_value) as avg_gini,
        max(gini_value) as max_gini,
        sum(case when gini_value >= 0.5 then 1 else 0 end) as high_inequality_dirs,
        sum(case when top_20_pct_share >= 0.7 then 1 else 0 end) as high_concentration_dirs
    from {{ ref('rollup_semgrep_directory_recursive_distributions') }}
    where run_pk = (select semgrep_run_pk from run_map)
      and metric = 'smell_count'
      and value_count >= 3
),
roslyn_summary as (
    select
        'roslyn' as tool,
        'violation_count' as metric,
        count(*) as directory_count,
        avg(gini_value) as avg_gini,
        max(gini_value) as max_gini,
        sum(case when gini_value >= 0.5 then 1 else 0 end) as high_inequality_dirs,
        sum(case when top_20_pct_share >= 0.7 then 1 else 0 end) as high_concentration_dirs
    from {{ ref('rollup_roslyn_directory_recursive_distributions') }}
    where run_pk = (select roslyn_run_pk from run_map)
      and metric = 'violation_count'
      and value_count >= 3
),
sonarqube_summary as (
    select
        'sonarqube' as tool,
        'issue_count' as metric,
        count(*) as directory_count,
        avg(gini_value) as avg_gini,
        max(gini_value) as max_gini,
        sum(case when gini_value >= 0.5 then 1 else 0 end) as high_inequality_dirs,
        sum(case when top_20_pct_share >= 0.7 then 1 else 0 end) as high_concentration_dirs
    from {{ ref('rollup_sonarqube_directory_recursive_distributions') }}
    where run_pk = (select sonarqube_run_pk from run_map)
      and metric = 'issue_count'
      and value_count >= 3
),
combined as (
    select * from scc_summary
    union all select * from lizard_summary
    union all select * from semgrep_summary
    union all select * from roslyn_summary
    union all select * from sonarqube_summary
),
totals as (
    select
        'TOTAL' as tool,
        'all' as metric,
        sum(directory_count) as directory_count,
        avg(avg_gini) as avg_gini,
        max(max_gini) as max_gini,
        sum(high_inequality_dirs) as high_inequality_dirs,
        sum(high_concentration_dirs) as high_concentration_dirs
    from combined
)
select
    tool,
    metric,
    directory_count,
    round(avg_gini, 3) as avg_gini,
    round(max_gini, 3) as max_gini,
    high_inequality_dirs,
    high_concentration_dirs,
    round(100.0 * high_inequality_dirs / nullif(directory_count, 0), 1) as pct_high_inequality,
    round(100.0 * high_concentration_dirs / nullif(directory_count, 0), 1) as pct_high_concentration,
    case
        when avg_gini < 0.3 then 'healthy'
        when avg_gini < 0.4 then 'moderate'
        when avg_gini < 0.5 then 'concerning'
        else 'unhealthy'
    end as overall_status
from (
    select * from combined
    union all
    select * from totals
)
order by
    case tool when 'TOTAL' then 'zzz' else tool end,
    metric
