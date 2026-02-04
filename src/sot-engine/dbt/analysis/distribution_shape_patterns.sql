{% set run_pk = var('run_pk') %}
{% set limit_rows = var('limit', 20) %}

-- Shape Pattern Analysis: Detect unusual distribution shapes that indicate code quality patterns
-- These patterns often indicate code smell accumulation in specific files.
--
-- Thresholds (based on statistical conventions):
--   - skewness > 2: Highly right-skewed (few files have much higher values than the rest)
--                   Normal distributions have skewness ~0; values >2 indicate significant asymmetry
--   - kurtosis > 6: Fat tails (extreme outliers present)
--                   Normal distributions have kurtosis ~3; values >6 indicate 2x normal tail weight
--   - cv > 1.5: High coefficient of variation (stddev exceeds 1.5x the mean)
--               Indicates inconsistent values across files in the directory
--
-- Severity escalation thresholds:
--   - skewness > 3: Extremely right-skewed
--   - kurtosis > 10: Extremely fat tails
--   - cv > 2: Extremely high variance

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
scc_shapes as (
    select
        directory_path,
        metric,
        value_count as file_count,
        skewness_value,
        kurtosis_value,
        cv_value,
        avg_value,
        stddev_value,
        min_value,
        max_value,
        p50_value,
        iqr_value,
        gini_value
    from {{ ref('rollup_scc_directory_recursive_distributions') }}
    where run_pk = (select scc_run_pk from run_map)
      and metric in ('lines_total', 'complexity', 'code_lines')
      and value_count >= 5
      and (skewness_value > 2 or kurtosis_value > 6 or cv_value > 1.5)
),
lizard_shapes as (
    select
        directory_path,
        metric,
        value_count as file_count,
        skewness_value,
        kurtosis_value,
        cv_value,
        avg_value,
        stddev_value,
        min_value,
        max_value,
        p50_value,
        iqr_value,
        gini_value
    from {{ ref('rollup_lizard_directory_recursive_distributions') }}
    where run_pk = (select lizard_run_pk from run_map)
      and metric in ('total_ccn', 'nloc', 'max_ccn', 'avg_ccn')
      and value_count >= 5
      and (skewness_value > 2 or kurtosis_value > 6 or cv_value > 1.5)
),
semgrep_shapes as (
    select
        directory_path,
        metric,
        value_count as file_count,
        skewness_value,
        kurtosis_value,
        cv_value,
        avg_value,
        stddev_value,
        min_value,
        max_value,
        p50_value,
        iqr_value,
        gini_value
    from {{ ref('rollup_semgrep_directory_recursive_distributions') }}
    where run_pk = (select semgrep_run_pk from run_map)
      and metric in ('smell_count', 'severity_high_plus')
      and value_count >= 5
      and (skewness_value > 2 or kurtosis_value > 6 or cv_value > 1.5)
),
roslyn_shapes as (
    select
        directory_path,
        metric,
        value_count as file_count,
        skewness_value,
        kurtosis_value,
        cv_value,
        avg_value,
        stddev_value,
        min_value,
        max_value,
        p50_value,
        iqr_value,
        gini_value
    from {{ ref('rollup_roslyn_directory_recursive_distributions') }}
    where run_pk = (select roslyn_run_pk from run_map)
      and metric in ('violation_count', 'severity_high_plus', 'cat_security', 'cat_design')
      and value_count >= 5
      and (skewness_value > 2 or kurtosis_value > 6 or cv_value > 1.5)
),
sonarqube_shapes as (
    select
        directory_path,
        metric,
        value_count as file_count,
        skewness_value,
        kurtosis_value,
        cv_value,
        avg_value,
        stddev_value,
        min_value,
        max_value,
        p50_value,
        iqr_value,
        gini_value
    from {{ ref('rollup_sonarqube_directory_recursive_distributions') }}
    where run_pk = (select sonarqube_run_pk from run_map)
      and metric in ('issue_count', 'severity_high_plus', 'complexity', 'cognitive_complexity')
      and value_count >= 5
      and (skewness_value > 2 or kurtosis_value > 6 or cv_value > 1.5)
),
combined as (
    select 'scc' as tool, * from scc_shapes
    union all
    select 'lizard' as tool, * from lizard_shapes
    union all
    select 'semgrep' as tool, * from semgrep_shapes
    union all
    select 'roslyn' as tool, * from roslyn_shapes
    union all
    select 'sonarqube' as tool, * from sonarqube_shapes
),
classified as (
    select
        *,
        -- Classify distribution shape
        case
            when skewness_value > 2 and kurtosis_value > 6 then 'highly skewed + fat tails'
            when skewness_value > 2 and cv_value > 1.5 then 'highly skewed + high variance'
            when kurtosis_value > 6 and cv_value > 1.5 then 'fat tails + high variance'
            when skewness_value > 3 then 'extremely right-skewed'
            when skewness_value > 2 then 'highly right-skewed'
            when kurtosis_value > 10 then 'extremely fat tails'
            when kurtosis_value > 6 then 'fat tails'
            when cv_value > 2 then 'extremely high variance'
            when cv_value > 1.5 then 'high variance'
            else 'unusual shape'
        end as shape_classification,
        -- Count concerning patterns present
        (
            case when skewness_value > 2 then 1 else 0 end +
            case when kurtosis_value > 6 then 1 else 0 end +
            case when cv_value > 1.5 then 1 else 0 end
        ) as pattern_count,
        -- Severity score based on magnitude
        (
            case when skewness_value > 3 then 2 when skewness_value > 2 then 1 else 0 end +
            case when kurtosis_value > 10 then 2 when kurtosis_value > 6 then 1 else 0 end +
            case when cv_value > 2 then 2 when cv_value > 1.5 then 1 else 0 end
        ) as severity_score
    from combined
),
ranked as (
    select
        *,
        row_number() over (
            partition by tool, metric
            order by severity_score desc, pattern_count desc, skewness_value desc, directory_path
        ) as rank_id
    from classified
)
select
    tool,
    directory_path,
    metric,
    file_count,
    round(skewness_value, 3) as skewness_value,
    round(kurtosis_value, 3) as kurtosis_value,
    round(cv_value, 3) as cv_value,
    round(avg_value, 2) as avg_value,
    round(stddev_value, 2) as stddev_value,
    round(min_value, 2) as min_value,
    round(max_value, 2) as max_value,
    round(p50_value, 2) as p50_value,
    round(iqr_value, 2) as iqr_value,
    round(gini_value, 3) as gini_value,
    shape_classification,
    pattern_count,
    severity_score,
    -- Interpretation guidance
    case
        when skewness_value > 2 then 'A few files have much higher values than the rest'
        when kurtosis_value > 6 then 'Contains extreme outlier values in the tails'
        when cv_value > 1.5 then 'Values are inconsistent across files (high spread relative to mean)'
        else 'Multiple unusual shape characteristics present'
    end as interpretation
from ranked
where rank_id <= {{ limit_rows }}
order by tool, metric, rank_id
