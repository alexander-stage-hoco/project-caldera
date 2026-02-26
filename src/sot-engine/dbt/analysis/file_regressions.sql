{% set repo_id = var('repo_id') %}
{% set limit_rows = var('limit', 100) %}

-- File-level regression detection between the two most recent runs
-- Shows files where quality metrics worsened

with repo_runs as (
    select
        cr.collection_run_id,
        cr.commit,
        cr.created_at,
        row_number() over (order by cr.created_at desc) as run_rank
    from {{ source('lz', 'lz_collection_runs') }} cr
    where cr.repo_id = '{{ repo_id }}'
      and cr.status = 'completed'
),

current_files as (
    select uf.*
    from {{ ref('unified_file_metrics') }} uf
    join repo_runs rr
        on rr.collection_run_id = uf.collection_run_id
        and rr.run_rank = 1
),

previous_files as (
    select uf.*
    from {{ ref('unified_file_metrics') }} uf
    join repo_runs rr
        on rr.collection_run_id = uf.collection_run_id
        and rr.run_rank = 2
),

file_deltas as (
    select
        coalesce(c.relative_path, p.relative_path) as relative_path,
        case
            when p.relative_path is null then 'added'
            when c.relative_path is null then 'removed'
            else 'modified'
        end as change_type,

        -- Complexity
        c.complexity_total_ccn as current_ccn,
        p.complexity_total_ccn as previous_ccn,
        coalesce(c.complexity_total_ccn, 0) - coalesce(p.complexity_total_ccn, 0) as delta_ccn,

        -- Coverage
        c.coverage_statement_pct as current_coverage,
        p.coverage_statement_pct as previous_coverage,
        coalesce(c.coverage_statement_pct, 0) - coalesce(p.coverage_statement_pct, 0) as delta_coverage,

        -- Violations (sum of all tools)
        coalesce(c.roslyn_violation_count, 0) + coalesce(c.semgrep_smell_count, 0)
            + coalesce(c.devskim_issue_count, 0) + coalesce(c.sonarqube_issue_count, 0)
            as current_total_issues,
        coalesce(p.roslyn_violation_count, 0) + coalesce(p.semgrep_smell_count, 0)
            + coalesce(p.devskim_issue_count, 0) + coalesce(p.sonarqube_issue_count, 0)
            as previous_total_issues,

        -- Duplication
        coalesce(c.pmd_cpd_duplicate_lines, 0) as current_dup_lines,
        coalesce(p.pmd_cpd_duplicate_lines, 0) as previous_dup_lines,

        -- Security
        coalesce(c.gitleaks_secret_count, 0) as current_secrets,
        coalesce(p.gitleaks_secret_count, 0) as previous_secrets,
        coalesce(c.trivy_total_finding_count, 0) as current_trivy,
        coalesce(p.trivy_total_finding_count, 0) as previous_trivy

    from current_files c
    full outer join previous_files p
        on p.relative_path = c.relative_path
)

select
    relative_path,
    change_type,
    delta_ccn,
    delta_coverage,
    current_total_issues - previous_total_issues as delta_issues,
    current_dup_lines - previous_dup_lines as delta_dup_lines,
    current_secrets - previous_secrets as delta_secrets,
    current_trivy - previous_trivy as delta_trivy,
    -- Composite regression score (higher = worse)
    case
        when change_type = 'removed' then 0
        else
            greatest(delta_ccn, 0) * 2
            + greatest(current_total_issues - previous_total_issues, 0)
            + greatest(-delta_coverage, 0)
            + greatest(current_secrets - previous_secrets, 0) * 10
            + greatest(current_trivy - previous_trivy, 0) * 5
    end as regression_score
from file_deltas
where change_type != 'removed'
  and (
    delta_ccn > 0
    or delta_coverage < 0
    or current_total_issues > previous_total_issues
    or current_dup_lines > previous_dup_lines
    or current_secrets > previous_secrets
    or current_trivy > previous_trivy
  )
order by regression_score desc
limit {{ limit_rows }}
