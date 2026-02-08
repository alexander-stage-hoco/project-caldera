-- Cross-tool composite file hotspots identifying files with multiple overlapping risk factors
-- Combines 5 risk dimensions: complexity, size, issues, coverage, coupling
-- Only includes files with 2+ medium or higher risk factors
-- Risk patterns classify the type of technical debt for prioritization

with file_metrics as (
    select
        collection_run_id,
        file_id,
        relative_path,
        directory_id,
        -- Size metrics (from SCC)
        loc_code,
        -- Complexity metrics (from Lizard)
        complexity_max as max_ccn,
        -- Coverage metrics (from dotCover)
        coverage_statement_pct,
        coverage_total_statements,
        -- Coupling metrics (from symbol-scanner)
        total_coupling,
        -- Issue counts - aggregate high+ severity from all issue tools
        coalesce(semgrep_severity_high_plus, 0) as semgrep_high_plus,
        coalesce(sonarqube_severity_high_plus, 0) as sonarqube_high_plus,
        coalesce(roslyn_severity_high_plus, 0) as roslyn_high_plus,
        coalesce(devskim_severity_high_plus, 0) as devskim_high_plus,
        -- Data availability flags
        loc_code is not null as has_size_data,
        complexity_max is not null as has_complexity_data,
        coverage_statement_pct is not null as has_coverage_data,
        total_coupling is not null as has_coupling_data,
        (semgrep_severity_high_plus is not null or
         sonarqube_severity_high_plus is not null or
         roslyn_severity_high_plus is not null or
         devskim_severity_high_plus is not null) as has_issues_data
    from {{ ref('unified_file_metrics') }}
),
scored_files as (
    select
        *,
        -- Total high+ issues across all issue tools
        coalesce(semgrep_high_plus, 0) +
        coalesce(sonarqube_high_plus, 0) +
        coalesce(roslyn_high_plus, 0) +
        coalesce(devskim_high_plus, 0) as total_high_plus_issues,

        -- Count available dimensions
        (case when has_size_data then 1 else 0 end +
         case when has_complexity_data then 1 else 0 end +
         case when has_coverage_data then 1 else 0 end +
         case when has_coupling_data then 1 else 0 end +
         case when has_issues_data then 1 else 0 end) as available_dimensions,

        -- Complexity risk (based on max_ccn)
        case
            when max_ccn is null then null
            when max_ccn > 50 then 'critical'
            when max_ccn > 20 then 'high'
            when max_ccn > 10 then 'medium'
            else 'low'
        end as complexity_risk,
        case
            when max_ccn is null then null
            when max_ccn > 50 then 4
            when max_ccn > 20 then 3
            when max_ccn > 10 then 2
            else 1
        end as complexity_score,

        -- Size risk (based on loc_code)
        case
            when loc_code is null then null
            when loc_code > 1000 then 'critical'
            when loc_code > 500 then 'high'
            when loc_code > 200 then 'medium'
            else 'low'
        end as size_risk,
        case
            when loc_code is null then null
            when loc_code > 1000 then 4
            when loc_code > 500 then 3
            when loc_code > 200 then 2
            else 1
        end as size_score,

        -- Coverage risk (inverted - lower coverage = higher risk)
        case
            when coverage_statement_pct is null then null
            when coverage_statement_pct < 20 then 'critical'
            when coverage_statement_pct < 40 then 'high'
            when coverage_statement_pct < 60 then 'medium'
            else 'low'
        end as coverage_risk,
        case
            when coverage_statement_pct is null then null
            when coverage_statement_pct < 20 then 4
            when coverage_statement_pct < 40 then 3
            when coverage_statement_pct < 60 then 2
            else 1
        end as coverage_score,

        -- Coupling risk (based on total_coupling)
        case
            when total_coupling is null then null
            when total_coupling >= 20 then 'critical'
            when total_coupling >= 10 then 'high'
            when total_coupling >= 5 then 'medium'
            else 'low'
        end as coupling_risk,
        case
            when total_coupling is null then null
            when total_coupling >= 20 then 4
            when total_coupling >= 10 then 3
            when total_coupling >= 5 then 2
            else 1
        end as coupling_score
    from file_metrics
),
with_issues_risk as (
    select
        *,
        -- Issues risk (based on total high+ count)
        case
            when not has_issues_data then null
            when total_high_plus_issues >= 10 then 'critical'
            when total_high_plus_issues >= 5 then 'high'
            when total_high_plus_issues >= 1 then 'medium'
            else 'low'
        end as issues_risk,
        case
            when not has_issues_data then null
            when total_high_plus_issues >= 10 then 4
            when total_high_plus_issues >= 5 then 3
            when total_high_plus_issues >= 1 then 2
            else 1
        end as issues_score
    from scored_files
),
composite_scored as (
    select
        *,
        -- Sum of all available scores
        coalesce(complexity_score, 0) +
        coalesce(size_score, 0) +
        coalesce(coverage_score, 0) +
        coalesce(coupling_score, 0) +
        coalesce(issues_score, 0) as total_score,

        -- Count of medium+ risks (score >= 2)
        (case when complexity_score >= 2 then 1 else 0 end +
         case when size_score >= 2 then 1 else 0 end +
         case when coverage_score >= 2 then 1 else 0 end +
         case when coupling_score >= 2 then 1 else 0 end +
         case when issues_score >= 2 then 1 else 0 end) as medium_plus_risk_count,

        -- Count of high+ risks (score >= 3)
        (case when complexity_score >= 3 then 1 else 0 end +
         case when size_score >= 3 then 1 else 0 end +
         case when coverage_score >= 3 then 1 else 0 end +
         case when coupling_score >= 3 then 1 else 0 end +
         case when issues_score >= 3 then 1 else 0 end) as high_plus_risk_count,

        -- Count of critical risks (score = 4)
        (case when complexity_score = 4 then 1 else 0 end +
         case when size_score = 4 then 1 else 0 end +
         case when coverage_score = 4 then 1 else 0 end +
         case when coupling_score = 4 then 1 else 0 end +
         case when issues_score = 4 then 1 else 0 end) as critical_risk_count
    from with_issues_risk
),
final_scored as (
    select
        *,
        -- Normalized composite score (0-100 scale)
        case
            when available_dimensions = 0 then null
            else round(
                (total_score::float / (available_dimensions * 4)) * 100,
                1
            )
        end as composite_score,

        -- Composite risk level based on counts
        case
            when critical_risk_count >= 2 then 'critical'
            when critical_risk_count >= 1 or high_plus_risk_count >= 2 then 'high'
            when high_plus_risk_count >= 1 or medium_plus_risk_count >= 2 then 'medium'
            else 'low'
        end as composite_risk_level,

        -- Risk pattern classification
        case
            -- Multi-dimension risk (3+ medium+ risks)
            when medium_plus_risk_count >= 3 then 'multi_dimension_risk'
            -- Complex + untested
            when (complexity_score >= 3 and coverage_score >= 3) then 'complex_untested'
            -- Complex + smelly
            when (complexity_score >= 3 and issues_score >= 2) then 'complex_smelly'
            -- God file (large + complex)
            when (size_score >= 3 and complexity_score >= 3) then 'god_file'
            -- Risky untested (issues + low coverage)
            when (issues_score >= 2 and coverage_score >= 3) then 'risky_untested'
            -- Coupled complex
            when (coupling_score >= 3 and complexity_score >= 3) then 'coupled_complex'
            -- Generic multi-risk
            when medium_plus_risk_count >= 2 then 'dual_risk'
            else 'single_risk'
        end as risk_pattern
    from composite_scored
)
select
    collection_run_id,
    file_id,
    relative_path,
    directory_id,
    -- Composite metrics
    composite_score,
    composite_risk_level,
    risk_pattern,
    medium_plus_risk_count,
    high_plus_risk_count,
    critical_risk_count,
    available_dimensions,
    total_score,
    -- Complexity dimension
    max_ccn,
    complexity_risk,
    complexity_score,
    -- Size dimension
    loc_code,
    size_risk,
    size_score,
    -- Issues dimension
    total_high_plus_issues,
    semgrep_high_plus,
    sonarqube_high_plus,
    roslyn_high_plus,
    devskim_high_plus,
    issues_risk,
    issues_score,
    -- Coverage dimension
    coverage_statement_pct,
    coverage_total_statements,
    coverage_risk,
    coverage_score,
    -- Coupling dimension
    total_coupling,
    coupling_risk,
    coupling_score,
    -- Data availability flags
    has_complexity_data,
    has_size_data,
    has_issues_data,
    has_coverage_data,
    has_coupling_data
from final_scored
where medium_plus_risk_count >= 2
order by collection_run_id, composite_score desc, medium_plus_risk_count desc
