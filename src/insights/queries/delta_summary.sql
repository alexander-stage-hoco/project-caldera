-- Delta summary: run-over-run comparison for the current run's repo
-- Returns one row with key deltas (or empty if no previous run exists)

WITH ranked_runs AS (
    SELECT
        cr.collection_run_id,
        cr.repo_id,
        cr.commit,
        cr.started_at,
        ROW_NUMBER() OVER (
            PARTITION BY cr.repo_id
            ORDER BY cr.started_at DESC
        ) AS run_rank
    FROM lz_collection_runs cr
    JOIN lz_tool_runs tr ON tr.collection_run_id = cr.collection_run_id
    WHERE tr.run_pk = ?
      AND cr.status IN ('completed', 'partial_success')
),

current_run AS (
    SELECT * FROM ranked_runs WHERE run_rank = 1
),

previous_run AS (
    SELECT * FROM ranked_runs WHERE run_rank = 2
),

current_agg AS (
    SELECT
        cr.collection_run_id,
        cr.commit,
        COUNT(*) AS total_files,
        SUM(uf.loc_code) AS total_code_lines,
        SUM(uf.complexity_total_ccn) AS total_ccn,
        AVG(uf.coverage_statement_pct) AS avg_coverage_pct,
        SUM(uf.gitleaks_secret_count) AS total_secrets,
        SUM(uf.trivy_total_finding_count) AS total_trivy
    FROM unified_file_metrics uf
    JOIN current_run cr ON cr.collection_run_id = uf.collection_run_id
    GROUP BY cr.collection_run_id, cr.commit
),

previous_agg AS (
    SELECT
        pr.collection_run_id,
        pr.commit,
        COUNT(*) AS total_files,
        SUM(uf.loc_code) AS total_code_lines,
        SUM(uf.complexity_total_ccn) AS total_ccn,
        AVG(uf.coverage_statement_pct) AS avg_coverage_pct,
        SUM(uf.gitleaks_secret_count) AS total_secrets,
        SUM(uf.trivy_total_finding_count) AS total_trivy
    FROM unified_file_metrics uf
    JOIN previous_run pr ON pr.collection_run_id = uf.collection_run_id
    GROUP BY pr.collection_run_id, pr.commit
),

current_quality AS (
    SELECT q.trust_score, q.warning_count, q.budget_passed
    FROM lz_run_quality_summary q
    JOIN current_run cr ON cr.collection_run_id = q.collection_run_id
),

previous_quality AS (
    SELECT q.trust_score, q.warning_count, q.budget_passed
    FROM lz_run_quality_summary q
    JOIN previous_run pr ON pr.collection_run_id = q.collection_run_id
)

SELECT
    c.commit AS current_commit,
    p.commit AS previous_commit,
    c.total_files AS current_files,
    p.total_files AS previous_files,
    c.total_files - p.total_files AS delta_files,
    c.total_code_lines - p.total_code_lines AS delta_code_lines,
    c.total_ccn - p.total_ccn AS delta_ccn,
    ROUND(c.avg_coverage_pct - p.avg_coverage_pct, 2) AS delta_coverage_pct,
    c.total_secrets - p.total_secrets AS delta_secrets,
    c.total_trivy - p.total_trivy AS delta_trivy,
    CASE WHEN c.total_ccn > p.total_ccn THEN TRUE ELSE FALSE END AS regression_complexity,
    CASE WHEN c.avg_coverage_pct < p.avg_coverage_pct THEN TRUE ELSE FALSE END AS regression_coverage,
    CASE WHEN c.total_secrets > p.total_secrets THEN TRUE ELSE FALSE END AS regression_secrets,
    CASE WHEN c.total_trivy > p.total_trivy THEN TRUE ELSE FALSE END AS regression_trivy,
    cq.trust_score - pq.trust_score AS delta_trust_score,
    CASE WHEN cq.trust_score < pq.trust_score THEN TRUE ELSE FALSE END AS regression_trust,
    CASE WHEN NOT cq.budget_passed AND pq.budget_passed THEN TRUE ELSE FALSE END AS regression_budget
FROM current_agg c
CROSS JOIN previous_agg p
LEFT JOIN current_quality cq ON TRUE
LEFT JOIN previous_quality pq ON TRUE
LIMIT 1
