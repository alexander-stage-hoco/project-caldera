{% set run_pk = var('run_pk') %}
{% set limit_rows = var('limit', 20) %}

-- Scope Comparison Analysis: Compare recursive vs direct rollups to find nested complexity
-- Identifies directories where metrics are significantly higher when including subdirectories.
-- These patterns reveal hidden complexity in subdirectory trees.
--
-- Thresholds (ratios comparing recursive vs direct values):
--   - gini_ratio > 1.5: Inequality increases >50% when including subdirectories
--   - p95_ratio > 2: 95th percentile doubles in subdirectory tree (hidden hotspots)
--   - avg_ratio > 2: Average doubles (significant hidden complexity)
--   - max_ratio > 2: Maximum doubles (extreme values buried in subdirectories)
--
-- Note: Ratios return NULL when denominator is 0 (undefined comparison).
-- These rows are excluded from flagged results.

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
scc_comparison as (
    select
        r.directory_path,
        r.metric,
        r.value_count as recursive_count,
        d.value_count as direct_count,
        r.avg_value as recursive_avg,
        d.avg_value as direct_avg,
        r.p95_value as recursive_p95,
        d.p95_value as direct_p95,
        r.max_value as recursive_max,
        d.max_value as direct_max,
        r.gini_value as recursive_gini,
        d.gini_value as direct_gini,
        r.stddev_value as recursive_stddev,
        d.stddev_value as direct_stddev
    from {{ ref('rollup_scc_directory_recursive_distributions') }} r
    join {{ ref('rollup_scc_directory_direct_distributions') }} d
        on r.directory_path = d.directory_path
        and r.metric = d.metric
        and d.run_pk = (select scc_run_pk from run_map)
    where r.run_pk = (select scc_run_pk from run_map)
      and r.metric in ('lines_total', 'complexity')
      and r.value_count >= 5
      and d.value_count >= 2
      and r.value_count > d.value_count  -- Has subdirectory files
),
lizard_comparison as (
    select
        r.directory_path,
        r.metric,
        r.value_count as recursive_count,
        d.value_count as direct_count,
        r.avg_value as recursive_avg,
        d.avg_value as direct_avg,
        r.p95_value as recursive_p95,
        d.p95_value as direct_p95,
        r.max_value as recursive_max,
        d.max_value as direct_max,
        r.gini_value as recursive_gini,
        d.gini_value as direct_gini,
        r.stddev_value as recursive_stddev,
        d.stddev_value as direct_stddev
    from {{ ref('rollup_lizard_directory_recursive_distributions') }} r
    join {{ ref('rollup_lizard_directory_direct_distributions') }} d
        on r.directory_path = d.directory_path
        and r.metric = d.metric
        and d.run_pk = (select lizard_run_pk from run_map)
    where r.run_pk = (select lizard_run_pk from run_map)
      and r.metric in ('total_ccn', 'nloc')
      and r.value_count >= 5
      and d.value_count >= 2
      and r.value_count > d.value_count
),
semgrep_comparison as (
    select
        r.directory_path,
        r.metric,
        r.value_count as recursive_count,
        d.value_count as direct_count,
        r.avg_value as recursive_avg,
        d.avg_value as direct_avg,
        r.p95_value as recursive_p95,
        d.p95_value as direct_p95,
        r.max_value as recursive_max,
        d.max_value as direct_max,
        r.gini_value as recursive_gini,
        d.gini_value as direct_gini,
        r.stddev_value as recursive_stddev,
        d.stddev_value as direct_stddev
    from {{ ref('rollup_semgrep_directory_recursive_distributions') }} r
    join {{ ref('rollup_semgrep_directory_direct_distributions') }} d
        on r.directory_path = d.directory_path
        and r.metric = d.metric
        and d.run_pk = (select semgrep_run_pk from run_map)
    where r.run_pk = (select semgrep_run_pk from run_map)
      and r.metric = 'smell_count'
      and r.value_count >= 5
      and d.value_count >= 2
      and r.value_count > d.value_count
),
roslyn_comparison as (
    select
        r.directory_path,
        r.metric,
        r.value_count as recursive_count,
        d.value_count as direct_count,
        r.avg_value as recursive_avg,
        d.avg_value as direct_avg,
        r.p95_value as recursive_p95,
        d.p95_value as direct_p95,
        r.max_value as recursive_max,
        d.max_value as direct_max,
        r.gini_value as recursive_gini,
        d.gini_value as direct_gini,
        r.stddev_value as recursive_stddev,
        d.stddev_value as direct_stddev
    from {{ ref('rollup_roslyn_directory_recursive_distributions') }} r
    join {{ ref('rollup_roslyn_directory_direct_distributions') }} d
        on r.directory_path = d.directory_path
        and r.metric = d.metric
        and d.run_pk = (select roslyn_run_pk from run_map)
    where r.run_pk = (select roslyn_run_pk from run_map)
      and r.metric = 'violation_count'
      and r.value_count >= 5
      and d.value_count >= 2
      and r.value_count > d.value_count
),
sonarqube_comparison as (
    select
        r.directory_path,
        r.metric,
        r.value_count as recursive_count,
        d.value_count as direct_count,
        r.avg_value as recursive_avg,
        d.avg_value as direct_avg,
        r.p95_value as recursive_p95,
        d.p95_value as direct_p95,
        r.max_value as recursive_max,
        d.max_value as direct_max,
        r.gini_value as recursive_gini,
        d.gini_value as direct_gini,
        r.stddev_value as recursive_stddev,
        d.stddev_value as direct_stddev
    from {{ ref('rollup_sonarqube_directory_recursive_distributions') }} r
    join {{ ref('rollup_sonarqube_directory_direct_distributions') }} d
        on r.directory_path = d.directory_path
        and r.metric = d.metric
        and d.run_pk = (select sonarqube_run_pk from run_map)
    where r.run_pk = (select sonarqube_run_pk from run_map)
      and r.metric in ('issue_count', 'complexity')
      and r.value_count >= 5
      and d.value_count >= 2
      and r.value_count > d.value_count
),
combined as (
    select 'scc' as tool, * from scc_comparison
    union all
    select 'lizard' as tool, * from lizard_comparison
    union all
    select 'semgrep' as tool, * from semgrep_comparison
    union all
    select 'roslyn' as tool, * from roslyn_comparison
    union all
    select 'sonarqube' as tool, * from sonarqube_comparison
),
with_ratios as (
    select
        *,
        recursive_count - direct_count as subdirectory_files,
        -- Return NULL for undefined ratios (denominator = 0) rather than 0,
        -- which could be confused with "no difference"
        case when direct_count > 0
            then cast(recursive_count as double) / direct_count
            else null end as count_ratio,
        case when direct_avg > 0
            then recursive_avg / direct_avg
            else null end as avg_ratio,
        case when direct_p95 > 0
            then recursive_p95 / direct_p95
            else null end as p95_ratio,
        case when direct_max > 0
            then recursive_max / direct_max
            else null end as max_ratio,
        case when direct_gini > 0
            then recursive_gini / direct_gini
            else null end as gini_ratio,
        case when direct_stddev > 0
            then recursive_stddev / direct_stddev
            else null end as stddev_ratio
    from combined
),
flagged as (
    select
        *,
        -- Flag significant discrepancies
        case when gini_ratio > 1.5 then 1 else 0 end as flag_gini_growth,
        case when p95_ratio > 2 then 1 else 0 end as flag_p95_hotspot,
        case when avg_ratio > 2 then 1 else 0 end as flag_avg_growth,
        case when max_ratio > 2 then 1 else 0 end as flag_max_growth,
        -- Count how many flags triggered
        (
            case when gini_ratio > 1.5 then 1 else 0 end +
            case when p95_ratio > 2 then 1 else 0 end +
            case when avg_ratio > 2 then 1 else 0 end +
            case when max_ratio > 2 then 1 else 0 end
        ) as flag_count,
        -- Composite severity score
        (
            case when gini_ratio > 2 then 2 when gini_ratio > 1.5 then 1 else 0 end +
            case when p95_ratio > 3 then 2 when p95_ratio > 2 then 1 else 0 end +
            case when avg_ratio > 3 then 2 when avg_ratio > 2 then 1 else 0 end
        ) as severity_score
    from with_ratios
    -- Exclude rows with NULL ratios (undefined comparisons)
    where (gini_ratio > 1.5 or p95_ratio > 2 or avg_ratio > 2 or max_ratio > 2)
      and gini_ratio is not null
      and avg_ratio is not null
),
ranked as (
    select
        *,
        row_number() over (
            partition by tool, metric
            order by severity_score desc, flag_count desc, gini_ratio desc, directory_path
        ) as rank_id
    from flagged
)
select
    tool,
    directory_path,
    metric,
    recursive_count,
    direct_count,
    subdirectory_files,
    round(count_ratio, 2) as count_ratio,
    round(recursive_avg, 2) as recursive_avg,
    round(direct_avg, 2) as direct_avg,
    round(avg_ratio, 2) as avg_ratio,
    round(recursive_p95, 2) as recursive_p95,
    round(direct_p95, 2) as direct_p95,
    round(p95_ratio, 2) as p95_ratio,
    round(recursive_gini, 3) as recursive_gini,
    round(direct_gini, 3) as direct_gini,
    round(gini_ratio, 2) as gini_ratio,
    round(recursive_max, 2) as recursive_max,
    round(direct_max, 2) as direct_max,
    round(max_ratio, 2) as max_ratio,
    flag_count,
    severity_score,
    case
        when gini_ratio > 1.5 and p95_ratio > 2 then 'nested inequality + hotspots'
        when gini_ratio > 1.5 and avg_ratio > 2 then 'nested inequality + higher averages'
        when p95_ratio > 2 and max_ratio > 2 then 'subdirectory hotspots + extreme values'
        when gini_ratio > 1.5 then 'inequality grows with depth'
        when p95_ratio > 2 then 'hotspots in subdirectories'
        when avg_ratio > 2 then 'higher complexity in subdirectories'
        when max_ratio > 2 then 'extreme values in subdirectories'
        else 'nested complexity detected'
    end as pattern_description,
    case
        when severity_score >= 4 then 'critical'
        when severity_score >= 2 then 'high'
        when flag_count >= 2 then 'moderate'
        else 'low'
    end as severity_level
from ranked
where rank_id <= {{ limit_rows }}
order by tool, metric, rank_id
