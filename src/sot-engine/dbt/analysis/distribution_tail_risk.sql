{% set run_pk = var('run_pk') %}
{% set limit_rows = var('limit', 20) %}

-- Tail Risk Analysis: Identify directories where a few files dominate the distribution
-- Flags directories with high concentration risk via percentiles and inequality metrics.
--
-- Thresholds:
--   - top_10_pct_share >= 0.5: Top 10% of files contain ≥50% of metric value
--                              Indicates extreme concentration - a few files hold most of the "debt"
--   - p99/p50 > 10: 99th percentile is 10x the median (extreme outliers)
--                   Signals presence of files far outside normal range
--   - palma_value > 5: Top 10% / bottom 40% ratio exceeds 5
--                      A Palma ratio >5 indicates high inequality (borrowed from economics)
--   - gini_value >= 0.5: Gini coefficient indicates moderate-to-high inequality
--                        Perfect equality = 0, perfect inequality = 1
--
-- Risk score weights:
--   - top_10_pct_share >= 0.5: +2 (most actionable - identifies specific files)
--   - p99_p50_ratio > 10: +2 (extreme outliers warrant investigation)
--   - palma_value > 5: +1 (supporting evidence of inequality)
--   - gini_value >= 0.5: +1 (supporting evidence of inequality)

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
scc_tail as (
    select
        directory_path,
        metric,
        value_count as file_count,
        p50_value,
        p95_value,
        p99_value,
        max_value,
        avg_value,
        top_10_pct_share,
        top_20_pct_share,
        palma_value,
        gini_value,
        case when p50_value > 0 then p99_value / p50_value else 0 end as p99_p50_ratio
    from {{ ref('rollup_scc_directory_recursive_distributions') }}
    where run_pk = (select scc_run_pk from run_map)
      and metric in ('lines_total', 'complexity')
      and value_count >= 5
      and (
          top_10_pct_share >= 0.5
          or (p50_value > 0 and p99_value / p50_value > 10)
          or palma_value > 5
      )
),
lizard_tail as (
    select
        directory_path,
        metric,
        value_count as file_count,
        p50_value,
        p95_value,
        p99_value,
        max_value,
        avg_value,
        top_10_pct_share,
        top_20_pct_share,
        palma_value,
        gini_value,
        case when p50_value > 0 then p99_value / p50_value else 0 end as p99_p50_ratio
    from {{ ref('rollup_lizard_directory_recursive_distributions') }}
    where run_pk = (select lizard_run_pk from run_map)
      and metric in ('total_ccn', 'nloc', 'max_ccn')
      and value_count >= 5
      and (
          top_10_pct_share >= 0.5
          or (p50_value > 0 and p99_value / p50_value > 10)
          or palma_value > 5
      )
),
semgrep_tail as (
    select
        directory_path,
        metric,
        value_count as file_count,
        p50_value,
        p95_value,
        p99_value,
        max_value,
        avg_value,
        top_10_pct_share,
        top_20_pct_share,
        palma_value,
        gini_value,
        case when p50_value > 0 then p99_value / p50_value else 0 end as p99_p50_ratio
    from {{ ref('rollup_semgrep_directory_recursive_distributions') }}
    where run_pk = (select semgrep_run_pk from run_map)
      and metric in ('smell_count', 'severity_high_plus')
      and value_count >= 5
      and (
          top_10_pct_share >= 0.5
          or (p50_value > 0 and p99_value / p50_value > 10)
          or palma_value > 5
      )
),
roslyn_tail as (
    select
        directory_path,
        metric,
        value_count as file_count,
        p50_value,
        p95_value,
        p99_value,
        max_value,
        avg_value,
        top_10_pct_share,
        top_20_pct_share,
        palma_value,
        gini_value,
        case when p50_value > 0 then p99_value / p50_value else 0 end as p99_p50_ratio
    from {{ ref('rollup_roslyn_directory_recursive_distributions') }}
    where run_pk = (select roslyn_run_pk from run_map)
      and metric in ('violation_count', 'severity_high_plus')
      and value_count >= 5
      and (
          top_10_pct_share >= 0.5
          or (p50_value > 0 and p99_value / p50_value > 10)
          or palma_value > 5
      )
),
sonarqube_tail as (
    select
        directory_path,
        metric,
        value_count as file_count,
        p50_value,
        p95_value,
        p99_value,
        max_value,
        avg_value,
        top_10_pct_share,
        top_20_pct_share,
        palma_value,
        gini_value,
        case when p50_value > 0 then p99_value / p50_value else 0 end as p99_p50_ratio
    from {{ ref('rollup_sonarqube_directory_recursive_distributions') }}
    where run_pk = (select sonarqube_run_pk from run_map)
      and metric in ('issue_count', 'severity_high_plus', 'complexity', 'cognitive_complexity')
      and value_count >= 5
      and (
          top_10_pct_share >= 0.5
          or (p50_value > 0 and p99_value / p50_value > 10)
          or palma_value > 5
      )
),
combined as (
    select 'scc' as tool, * from scc_tail
    union all
    select 'lizard' as tool, * from lizard_tail
    union all
    select 'semgrep' as tool, * from semgrep_tail
    union all
    select 'roslyn' as tool, * from roslyn_tail
    union all
    select 'sonarqube' as tool, * from sonarqube_tail
),
scored as (
    select
        *,
        -- Composite tail risk score: higher = more concerning
        (
            case when top_10_pct_share >= 0.5 then 2 else 0 end +
            case when p99_p50_ratio > 10 then 2 else 0 end +
            case when palma_value > 5 then 1 else 0 end +
            case when gini_value >= 0.5 then 1 else 0 end
        ) as risk_score
    from combined
),
ranked as (
    select
        *,
        row_number() over (
            partition by tool, metric
            order by risk_score desc, top_10_pct_share desc, p99_p50_ratio desc, directory_path
        ) as rank_id
    from scored
)
select
    tool,
    directory_path,
    metric,
    file_count,
    round(p50_value, 2) as p50_value,
    round(p95_value, 2) as p95_value,
    round(p99_value, 2) as p99_value,
    round(max_value, 2) as max_value,
    round(avg_value, 2) as avg_value,
    round(p99_p50_ratio, 2) as p99_p50_ratio,
    round(top_10_pct_share, 3) as top_10_pct_share,
    round(top_20_pct_share, 3) as top_20_pct_share,
    round(palma_value, 2) as palma_value,
    round(gini_value, 3) as gini_value,
    risk_score,
    case
        when top_10_pct_share >= 0.5 and p99_p50_ratio > 10 then 'extreme concentration + outliers'
        when top_10_pct_share >= 0.5 then 'extreme concentration'
        when p99_p50_ratio > 10 then 'extreme outliers'
        when palma_value > 5 then 'high palma ratio'
        else 'elevated tail risk'
    end as risk_pattern
from ranked
where rank_id <= {{ limit_rows }}
order by tool, metric, rank_id
