-- Claim support: pervasive code smells
-- Detects smell types affecting > 50% of files
-- Used by PervasiveDebtRule

WITH run_map AS (
    SELECT
        tr_scc.run_pk AS scc_run_pk,
        tr_semgrep.run_pk AS semgrep_run_pk
    FROM lz_tool_runs tr_scc
    LEFT JOIN lz_tool_runs tr_semgrep
        ON tr_semgrep.collection_run_id = tr_scc.collection_run_id
        AND tr_semgrep.tool_name = 'semgrep'
    WHERE tr_scc.run_pk = {{ run_pk }}
),
total_files AS (
    SELECT COUNT(*) AS cnt
    FROM unified_file_metrics
    WHERE run_pk = (SELECT scc_run_pk FROM run_map)
      AND loc_total > 0
),
smell_distribution AS (
    SELECT
        sfm.rule_id AS smell_type,
        COUNT(DISTINCT sfm.relative_path) AS affected_files,
        SUM(sfm.finding_count) AS total_findings
    FROM stg_semgrep_file_metrics sfm
    WHERE sfm.run_pk = (SELECT semgrep_run_pk FROM run_map)
    GROUP BY sfm.rule_id
)
SELECT
    sd.smell_type,
    sd.affected_files,
    sd.total_findings,
    tf.cnt AS total_files,
    ROUND(sd.affected_files * 100.0 / NULLIF(tf.cnt, 0), 1) AS affected_pct
FROM smell_distribution sd
CROSS JOIN total_files tf
WHERE sd.affected_files * 100.0 / NULLIF(tf.cnt, 0) > {{ pct_threshold | default(50) }}
ORDER BY affected_pct DESC
