{% set run_pk = var('run_pk') %}
{% set limit_rows = var('limit', 30) %}

-- Module health scores combining metrics from all 5 tools
-- Higher scores indicate healthier directories (lower inequality)

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
scc_metrics as (
    select
        directory_path,
        max(case when metric = 'lines_total' then gini_value end) as loc_gini,
        max(case when metric = 'complexity' then gini_value end) as scc_complexity_gini,
        max(case when metric = 'lines_total' then value_count end) as file_count
    from {{ ref('rollup_scc_directory_recursive_distributions') }}
    where run_pk = (select scc_run_pk from run_map)
      and metric in ('lines_total', 'complexity')
    group by directory_path
),
lizard_metrics as (
    select
        directory_path,
        max(case when metric = 'total_ccn' then gini_value end) as ccn_gini,
        max(case when metric = 'nloc' then gini_value end) as nloc_gini
    from {{ ref('rollup_lizard_directory_recursive_distributions') }}
    where run_pk = (select lizard_run_pk from run_map)
      and metric in ('total_ccn', 'nloc')
    group by directory_path
),
semgrep_metrics as (
    select
        directory_path,
        max(case when metric = 'smell_count' then gini_value end) as smell_gini
    from {{ ref('rollup_semgrep_directory_recursive_distributions') }}
    where run_pk = (select semgrep_run_pk from run_map)
      and metric = 'smell_count'
    group by directory_path
),
roslyn_metrics as (
    select
        directory_path,
        max(case when metric = 'violation_count' then gini_value end) as violation_gini
    from {{ ref('rollup_roslyn_directory_recursive_distributions') }}
    where run_pk = (select roslyn_run_pk from run_map)
      and metric = 'violation_count'
    group by directory_path
),
sonarqube_metrics as (
    select
        directory_path,
        max(case when metric = 'issue_count' then gini_value end) as issue_gini
    from {{ ref('rollup_sonarqube_directory_recursive_distributions') }}
    where run_pk = (select sonarqube_run_pk from run_map)
      and metric = 'issue_count'
    group by directory_path
),
combined as (
    select
        s.directory_path,
        s.file_count,
        s.loc_gini,
        s.scc_complexity_gini,
        l.ccn_gini,
        l.nloc_gini,
        sm.smell_gini,
        r.violation_gini,
        sq.issue_gini,
        -- Count how many metrics are available
        (case when s.loc_gini is not null then 1 else 0 end
         + case when l.ccn_gini is not null then 1 else 0 end
         + case when sm.smell_gini is not null then 1 else 0 end
         + case when r.violation_gini is not null then 1 else 0 end
         + case when sq.issue_gini is not null then 1 else 0 end) as metric_count,
        -- Average Gini across all available metrics (lower is healthier)
        (coalesce(s.loc_gini, 0) + coalesce(l.ccn_gini, 0) + coalesce(sm.smell_gini, 0)
         + coalesce(r.violation_gini, 0) + coalesce(sq.issue_gini, 0))
        / nullif(
            (case when s.loc_gini is not null then 1 else 0 end
             + case when l.ccn_gini is not null then 1 else 0 end
             + case when sm.smell_gini is not null then 1 else 0 end
             + case when r.violation_gini is not null then 1 else 0 end
             + case when sq.issue_gini is not null then 1 else 0 end), 0
        ) as avg_gini
    from scc_metrics s
    left join lizard_metrics l on l.directory_path = s.directory_path
    left join semgrep_metrics sm on sm.directory_path = s.directory_path
    left join roslyn_metrics r on r.directory_path = s.directory_path
    left join sonarqube_metrics sq on sq.directory_path = s.directory_path
    where s.file_count >= 3
),
scored as (
    select
        *,
        -- Health score: 100 - (avg_gini * 100), so lower inequality = higher score
        round(100 - (avg_gini * 100), 1) as health_score,
        row_number() over (order by avg_gini asc, file_count desc, directory_path) as healthy_rank,
        row_number() over (order by avg_gini desc, file_count desc, directory_path) as unhealthy_rank
    from combined
    where metric_count >= 2  -- Require at least 2 tools for meaningful comparison
)
select
    directory_path,
    file_count,
    health_score,
    metric_count as tools_contributing,
    round(avg_gini, 3) as avg_gini,
    round(loc_gini, 3) as loc_gini,
    round(ccn_gini, 3) as ccn_gini,
    round(smell_gini, 3) as smell_gini,
    round(violation_gini, 3) as violation_gini,
    round(issue_gini, 3) as issue_gini,
    case
        when health_score >= 80 then 'healthy'
        when health_score >= 60 then 'moderate'
        when health_score >= 40 then 'concerning'
        else 'unhealthy'
    end as health_level,
    healthy_rank,
    unhealthy_rank
from scored
where healthy_rank <= {{ limit_rows }} or unhealthy_rank <= {{ limit_rows }}
order by health_score desc, file_count desc
