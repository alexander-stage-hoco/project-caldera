{% set run_pk = var('run_pk') %}
{% set limit_rows = var('limit', 20) %}

-- Directories with high Gini inequality across all 5 tools
-- Gini >= 0.3 indicates moderate inequality, >= 0.5 is high

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
scc_gini as (
    select
        directory_path,
        metric,
        gini_value,
        value_count as file_count,
        avg_value,
        max_value,
        top_10_pct_share,
        top_20_pct_share
    from {{ ref('rollup_scc_directory_recursive_distributions') }}
    where run_pk = (select scc_run_pk from run_map)
      and metric in ('lines_total', 'complexity')
      and gini_value >= 0.3
      and value_count >= 3
),
lizard_gini as (
    select
        directory_path,
        metric,
        gini_value,
        value_count as file_count,
        avg_value,
        max_value,
        top_10_pct_share,
        top_20_pct_share
    from {{ ref('rollup_lizard_directory_recursive_distributions') }}
    where run_pk = (select lizard_run_pk from run_map)
      and metric in ('total_ccn', 'nloc')
      and gini_value >= 0.3
      and value_count >= 3
),
semgrep_gini as (
    select
        directory_path,
        metric,
        gini_value,
        value_count as file_count,
        avg_value,
        max_value,
        top_10_pct_share,
        top_20_pct_share
    from {{ ref('rollup_semgrep_directory_recursive_distributions') }}
    where run_pk = (select semgrep_run_pk from run_map)
      and metric = 'smell_count'
      and gini_value >= 0.3
      and value_count >= 3
),
roslyn_gini as (
    select
        directory_path,
        metric,
        gini_value,
        value_count as file_count,
        avg_value,
        max_value,
        top_10_pct_share,
        top_20_pct_share
    from {{ ref('rollup_roslyn_directory_recursive_distributions') }}
    where run_pk = (select roslyn_run_pk from run_map)
      and metric = 'violation_count'
      and gini_value >= 0.3
      and value_count >= 3
),
sonarqube_gini as (
    select
        directory_path,
        metric,
        gini_value,
        value_count as file_count,
        avg_value,
        max_value,
        top_10_pct_share,
        top_20_pct_share
    from {{ ref('rollup_sonarqube_directory_recursive_distributions') }}
    where run_pk = (select sonarqube_run_pk from run_map)
      and metric = 'issue_count'
      and gini_value >= 0.3
      and value_count >= 3
),
combined as (
    select 'scc' as tool, * from scc_gini
    union all
    select 'lizard' as tool, * from lizard_gini
    union all
    select 'semgrep' as tool, * from semgrep_gini
    union all
    select 'roslyn' as tool, * from roslyn_gini
    union all
    select 'sonarqube' as tool, * from sonarqube_gini
),
ranked as (
    select
        *,
        row_number() over (
            partition by tool, metric
            order by gini_value desc, file_count desc, directory_path
        ) as rank_id
    from combined
)
select
    tool,
    directory_path,
    metric,
    round(gini_value, 3) as gini_value,
    file_count,
    round(avg_value, 2) as avg_value,
    round(max_value, 2) as max_value,
    round(top_10_pct_share, 3) as top_10_pct_share,
    round(top_20_pct_share, 3) as top_20_pct_share,
    case
        when gini_value >= 0.5 then 'high'
        when gini_value >= 0.4 then 'moderate-high'
        else 'moderate'
    end as inequality_level
from ranked
where rank_id <= {{ limit_rows }}
order by tool, metric, rank_id
