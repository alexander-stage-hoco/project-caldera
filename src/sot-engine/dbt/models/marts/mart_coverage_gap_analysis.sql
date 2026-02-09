-- Coverage Gap Analysis: Identifies high-risk files with low test coverage
-- Joins coverage data with complexity metrics to prioritize testing efforts
--
-- Risk score formula: (normalized_ccn * 0.6) + ((100 - line_coverage_pct) * 0.4)
-- Files are ranked by risk score descending

with coverage as (
    select
        run_pk,
        file_id,
        directory_id,
        relative_path,
        line_coverage_pct,
        branch_coverage_pct,
        lines_total,
        lines_covered,
        lines_missed,
        branches_total,
        branches_covered,
        source_format
    from {{ ref('stg_lz_coverage_summary') }}
),

lizard as (
    select
        run_pk,
        file_id,
        relative_path,
        nloc,
        function_count,
        total_ccn,
        avg_ccn,
        max_ccn
    from {{ source('lz', 'lz_lizard_file_metrics') }}
),

-- Get max CCN for normalization (per run)
max_ccn_per_run as (
    select
        run_pk,
        max(max_ccn) as run_max_ccn
    from lizard
    group by run_pk
),

-- Join coverage with complexity
coverage_with_complexity as (
    select
        c.run_pk,
        c.file_id,
        c.directory_id,
        c.relative_path,
        c.line_coverage_pct,
        c.branch_coverage_pct,
        c.lines_total,
        c.lines_covered,
        c.lines_missed,
        c.source_format,
        l.nloc,
        l.function_count,
        l.total_ccn,
        l.avg_ccn,
        l.max_ccn,
        m.run_max_ccn
    from coverage c
    left join lizard l
        on c.run_pk = l.run_pk and c.file_id = l.file_id
    left join max_ccn_per_run m
        on c.run_pk = m.run_pk
),

-- Calculate risk scores
risk_scores as (
    select
        *,
        -- Normalize CCN to 0-100 scale
        case
            when run_max_ccn > 0 and max_ccn is not null
            then (max_ccn * 100.0 / run_max_ccn)
            else 0
        end as ccn_normalized,
        -- Coverage deficit (100 - coverage%)
        case
            when line_coverage_pct is not null
            then 100 - line_coverage_pct
            else 100  -- Assume worst case if no coverage data
        end as coverage_deficit,
        -- Risk score: weighted combination of complexity and coverage deficit
        case
            when run_max_ccn > 0 and max_ccn is not null and line_coverage_pct is not null
            then round(
                ((max_ccn * 100.0 / run_max_ccn) * 0.6) +
                ((100 - line_coverage_pct) * 0.4),
                2
            )
            when line_coverage_pct is not null
            then round((100 - line_coverage_pct) * 0.4, 2)
            else 100  -- Maximum risk if no data
        end as risk_score
    from coverage_with_complexity
)

select
    run_pk,
    file_id,
    directory_id,
    relative_path,
    line_coverage_pct,
    branch_coverage_pct,
    lines_total,
    lines_covered,
    lines_missed,
    source_format,
    nloc,
    function_count,
    total_ccn,
    avg_ccn,
    max_ccn,
    ccn_normalized,
    coverage_deficit,
    risk_score,
    -- Risk tier classification
    case
        when risk_score >= 80 then 'CRITICAL'
        when risk_score >= 60 then 'HIGH'
        when risk_score >= 40 then 'MEDIUM'
        when risk_score >= 20 then 'LOW'
        else 'MINIMAL'
    end as risk_tier,
    row_number() over (partition by run_pk order by risk_score desc) as risk_rank
from risk_scores
where lines_total > 0  -- Exclude files with no coverable lines
order by run_pk, risk_score desc
