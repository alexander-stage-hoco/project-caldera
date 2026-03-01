-- Top file regressions between current and previous run
-- Returns the worst-regressing files for the current run's repo

WITH ranked_runs AS (
    SELECT
        cr.collection_run_id,
        cr.repo_id,
        ROW_NUMBER() OVER (
            PARTITION BY cr.repo_id
            ORDER BY cr.started_at DESC
        ) AS run_rank
    FROM lz_collection_runs cr
    JOIN lz_tool_runs tr ON tr.collection_run_id = cr.collection_run_id
    WHERE tr.run_pk = ?
      AND cr.status IN ('completed', 'partial_success')
),

current_files AS (
    SELECT uf.*
    FROM unified_file_metrics uf
    JOIN ranked_runs rr
        ON rr.collection_run_id = uf.collection_run_id
        AND rr.run_rank = 1
),

previous_files AS (
    SELECT uf.*
    FROM unified_file_metrics uf
    JOIN ranked_runs rr
        ON rr.collection_run_id = uf.collection_run_id
        AND rr.run_rank = 2
),

file_deltas AS (
    SELECT
        COALESCE(c.relative_path, p.relative_path) AS relative_path,
        CASE
            WHEN p.relative_path IS NULL THEN 'new'
            WHEN c.relative_path IS NULL THEN 'resolved'
            ELSE 'existing'
        END AS change_type,
        COALESCE(c.complexity_total_ccn, 0) - COALESCE(p.complexity_total_ccn, 0) AS delta_ccn,
        COALESCE(c.coverage_statement_pct, 0) - COALESCE(p.coverage_statement_pct, 0) AS delta_coverage,
        (COALESCE(c.roslyn_violation_count, 0) + COALESCE(c.semgrep_smell_count, 0)
            + COALESCE(c.devskim_issue_count, 0) + COALESCE(c.sonarqube_issue_count, 0))
        - (COALESCE(p.roslyn_violation_count, 0) + COALESCE(p.semgrep_smell_count, 0)
            + COALESCE(p.devskim_issue_count, 0) + COALESCE(p.sonarqube_issue_count, 0))
            AS delta_issues,
        COALESCE(c.gitleaks_secret_count, 0) - COALESCE(p.gitleaks_secret_count, 0) AS delta_secrets,
        COALESCE(c.trivy_total_finding_count, 0) - COALESCE(p.trivy_total_finding_count, 0) AS delta_trivy
    FROM current_files c
    FULL OUTER JOIN previous_files p
        ON p.relative_path = c.relative_path
)

SELECT
    relative_path,
    change_type,
    delta_ccn,
    delta_coverage,
    delta_issues,
    delta_secrets,
    delta_trivy,
    GREATEST(delta_ccn, 0) * 2
        + GREATEST(delta_issues, 0)
        + GREATEST(-delta_coverage, 0)
        + GREATEST(delta_secrets, 0) * 10
        + GREATEST(delta_trivy, 0) * 5
        AS regression_score
FROM file_deltas
WHERE change_type != 'resolved'
  AND (delta_ccn > 0 OR delta_issues > 0 OR delta_secrets > 0 OR delta_trivy > 0 OR delta_coverage < -5)
ORDER BY regression_score DESC
LIMIT 20
