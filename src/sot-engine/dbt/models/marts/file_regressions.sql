-- File-level regression detection between consecutive runs.
-- Materializes per-file quality deltas with classification.

with ranked_runs as (
    select
        cr.collection_run_id,
        cr.repo_id,
        cr.commit,
        cr.started_at,
        row_number() over (
            partition by cr.repo_id
            order by cr.started_at desc
        ) as run_rank
    from {{ source('lz', 'lz_collection_runs') }} cr
    where cr.status in ('completed', 'partial_success')
),

current_files as (
    select uf.*, rr.repo_id
    from {{ ref('unified_file_metrics') }} uf
    join ranked_runs rr
        on rr.collection_run_id = uf.collection_run_id
        and rr.run_rank = 1
),

previous_files as (
    select uf.*, rr.repo_id
    from {{ ref('unified_file_metrics') }} uf
    join ranked_runs rr
        on rr.collection_run_id = uf.collection_run_id
        and rr.run_rank = 2
),

file_deltas as (
    select
        coalesce(c.repo_id, p.repo_id) as repo_id,
        coalesce(c.collection_run_id, p.collection_run_id) as collection_run_id,
        coalesce(c.relative_path, p.relative_path) as relative_path,
        case
            when p.relative_path is null then 'new'
            when c.relative_path is null then 'resolved'
            else 'existing'
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
        and p.repo_id = c.repo_id
)

select
    repo_id,
    collection_run_id,
    relative_path,
    change_type,
    delta_ccn,
    delta_coverage,
    current_total_issues - previous_total_issues as delta_issues,
    current_dup_lines - previous_dup_lines as delta_dup_lines,
    current_secrets - previous_secrets as delta_secrets,
    current_trivy - previous_trivy as delta_trivy,

    -- Classification: worsened, improved, or unchanged
    case
        when change_type = 'resolved' then 'resolved'
        when change_type = 'new' and (
            coalesce(current_total_issues, 0) > 0
            or coalesce(current_secrets, 0) > 0
            or coalesce(current_trivy, 0) > 0
        ) then 'new'
        when (
            delta_ccn > 0
            or (current_total_issues - previous_total_issues) > 0
            or (current_secrets - previous_secrets) > 0
            or (current_trivy - previous_trivy) > 0
            or delta_coverage < -5
        ) then 'worsened'
        when (
            delta_ccn < 0
            or (current_total_issues - previous_total_issues) < 0
            or (current_secrets - previous_secrets) < 0
            or (current_trivy - previous_trivy) < 0
            or delta_coverage > 5
        ) then 'improved'
        else 'unchanged'
    end as regression_classification,

    -- Composite regression score (higher = worse)
    case
        when change_type = 'resolved' then 0
        else
            greatest(delta_ccn, 0) * 2
            + greatest(current_total_issues - previous_total_issues, 0)
            + greatest(-delta_coverage, 0)
            + greatest(current_secrets - previous_secrets, 0) * 10
            + greatest(current_trivy - previous_trivy, 0) * 5
    end as regression_score
from file_deltas
where change_type != 'resolved'
  or (
    delta_ccn != 0
    or current_total_issues != previous_total_issues
    or current_dup_lines != previous_dup_lines
    or current_secrets != previous_secrets
    or current_trivy != previous_trivy
  )
