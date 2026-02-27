{% set repo_id = var('repo_id') %}
{% set limit_rows = var('limit', 50) %}

-- Run-over-run comparison for a repository
-- Shows deltas between the two most recent collection runs
-- Detects regressions: new violations, coverage drops, complexity increases

with repo_runs as (
    select
        cr.collection_run_id,
        cr.repo_id,
        cr.commit,
        cr.created_at,
        row_number() over (order by cr.created_at desc) as run_rank
    from {{ source('lz', 'lz_collection_runs') }} cr
    where cr.repo_id = '{{ repo_id }}'
      and cr.status = 'completed'
),

current_run as (
    select collection_run_id from repo_runs where run_rank = 1
),

previous_run as (
    select collection_run_id from repo_runs where run_rank = 2
),

-- Aggregate file-level metrics per run
current_summary as (
    select
        'current' as run_label,
        cr.collection_run_id,
        rr.commit,
        rr.created_at,
        count(*) as total_files,
        sum(uf.loc_code) as total_code_lines,
        sum(uf.complexity_total_ccn) as total_ccn,
        avg(uf.complexity_avg) as avg_ccn,
        max(uf.complexity_max) as max_ccn,
        sum(case when uf.coverage_statement_pct is not null then 1 else 0 end) as files_with_coverage,
        avg(uf.coverage_statement_pct) as avg_coverage_pct,
        sum(uf.roslyn_violation_count) as total_roslyn_violations,
        sum(uf.roslyn_severity_high_plus) as total_roslyn_high_plus,
        sum(uf.semgrep_smell_count) as total_semgrep_smells,
        sum(uf.semgrep_severity_high_plus) as total_semgrep_high_plus,
        sum(uf.devskim_issue_count) as total_devskim_issues,
        sum(uf.gitleaks_secret_count) as total_gitleaks_secrets,
        sum(uf.trivy_total_finding_count) as total_trivy_findings,
        sum(uf.pmd_cpd_duplicate_lines) as total_duplicate_lines,
        sum(uf.sonarqube_issue_count) as total_sonarqube_issues,
        sum(uf.sonarqube_cognitive_complexity) as total_cognitive_complexity
    from {{ ref('unified_file_metrics') }} uf
    join current_run cr on cr.collection_run_id = uf.collection_run_id
    join repo_runs rr on rr.collection_run_id = cr.collection_run_id
    group by cr.collection_run_id, rr.commit, rr.created_at
),

previous_summary as (
    select
        'previous' as run_label,
        pr.collection_run_id,
        rr.commit,
        rr.created_at,
        count(*) as total_files,
        sum(uf.loc_code) as total_code_lines,
        sum(uf.complexity_total_ccn) as total_ccn,
        avg(uf.complexity_avg) as avg_ccn,
        max(uf.complexity_max) as max_ccn,
        sum(case when uf.coverage_statement_pct is not null then 1 else 0 end) as files_with_coverage,
        avg(uf.coverage_statement_pct) as avg_coverage_pct,
        sum(uf.roslyn_violation_count) as total_roslyn_violations,
        sum(uf.roslyn_severity_high_plus) as total_roslyn_high_plus,
        sum(uf.semgrep_smell_count) as total_semgrep_smells,
        sum(uf.semgrep_severity_high_plus) as total_semgrep_high_plus,
        sum(uf.devskim_issue_count) as total_devskim_issues,
        sum(uf.gitleaks_secret_count) as total_gitleaks_secrets,
        sum(uf.trivy_total_finding_count) as total_trivy_findings,
        sum(uf.pmd_cpd_duplicate_lines) as total_duplicate_lines,
        sum(uf.sonarqube_issue_count) as total_sonarqube_issues,
        sum(uf.sonarqube_cognitive_complexity) as total_cognitive_complexity
    from {{ ref('unified_file_metrics') }} uf
    join previous_run pr on pr.collection_run_id = uf.collection_run_id
    join repo_runs rr on rr.collection_run_id = pr.collection_run_id
    group by pr.collection_run_id, rr.commit, rr.created_at
)

select
    c.commit as current_commit,
    p.commit as previous_commit,
    c.created_at as current_run_at,
    p.created_at as previous_run_at,

    -- File count delta
    c.total_files as current_files,
    p.total_files as previous_files,
    c.total_files - p.total_files as delta_files,

    -- Code size delta
    c.total_code_lines as current_code_lines,
    p.total_code_lines as previous_code_lines,
    c.total_code_lines - p.total_code_lines as delta_code_lines,

    -- Complexity deltas
    c.total_ccn as current_total_ccn,
    p.total_ccn as previous_total_ccn,
    c.total_ccn - p.total_ccn as delta_total_ccn,
    round(c.avg_ccn, 2) as current_avg_ccn,
    round(p.avg_ccn, 2) as previous_avg_ccn,
    round(c.avg_ccn - p.avg_ccn, 2) as delta_avg_ccn,
    c.max_ccn as current_max_ccn,
    p.max_ccn as previous_max_ccn,

    -- Coverage deltas
    round(c.avg_coverage_pct, 2) as current_avg_coverage_pct,
    round(p.avg_coverage_pct, 2) as previous_avg_coverage_pct,
    round(c.avg_coverage_pct - p.avg_coverage_pct, 2) as delta_coverage_pct,

    -- Violation deltas (positive = regression)
    c.total_roslyn_violations - p.total_roslyn_violations as delta_roslyn_violations,
    c.total_roslyn_high_plus - p.total_roslyn_high_plus as delta_roslyn_high_plus,
    c.total_semgrep_smells - p.total_semgrep_smells as delta_semgrep_smells,
    c.total_semgrep_high_plus - p.total_semgrep_high_plus as delta_semgrep_high_plus,
    c.total_devskim_issues - p.total_devskim_issues as delta_devskim_issues,
    c.total_gitleaks_secrets - p.total_gitleaks_secrets as delta_gitleaks_secrets,
    c.total_trivy_findings - p.total_trivy_findings as delta_trivy_findings,
    c.total_duplicate_lines - p.total_duplicate_lines as delta_duplicate_lines,
    c.total_sonarqube_issues - p.total_sonarqube_issues as delta_sonarqube_issues,
    c.total_cognitive_complexity - p.total_cognitive_complexity as delta_cognitive_complexity,

    -- Regression flags
    case when c.total_ccn > p.total_ccn then true else false end as regression_complexity,
    case when c.avg_coverage_pct < p.avg_coverage_pct then true else false end as regression_coverage,
    case when c.total_roslyn_high_plus > p.total_roslyn_high_plus then true else false end as regression_roslyn_high,
    case when c.total_semgrep_high_plus > p.total_semgrep_high_plus then true else false end as regression_semgrep_high,
    case when c.total_gitleaks_secrets > p.total_gitleaks_secrets then true else false end as regression_secrets,
    case when c.total_trivy_findings > p.total_trivy_findings then true else false end as regression_trivy,
    case when c.total_duplicate_lines > p.total_duplicate_lines then true else false end as regression_duplication

from current_summary c
cross join previous_summary p
limit {{ limit_rows }}
