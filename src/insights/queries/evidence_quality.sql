-- Evidence: code quality issues
-- Finds files with high smell + issue density from unified_file_metrics
-- Used by EvidenceCollector to populate quality evidence items

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
file_smells AS (
    SELECT
        ufm.relative_path,
        ufm.loc_total,
        ufm.smell_count,
        ufm.issue_count,
        ROUND(ufm.smell_count * 1000.0 / NULLIF(ufm.loc_total, 0), 1) AS smell_density_per_kloc,
        ROUND(ufm.issue_count * 1000.0 / NULLIF(ufm.loc_total, 0), 1) AS issue_density_per_kloc,
        (SELECT scc_run_pk FROM run_map) AS tool_run_pk
    FROM unified_file_metrics ufm
    WHERE ufm.run_pk = (SELECT scc_run_pk FROM run_map)
      AND (ufm.smell_count > 0 OR ufm.issue_count > 0)
      AND ufm.loc_total > 50
)
SELECT *
FROM file_smells
WHERE smell_density_per_kloc >= {{ density_threshold | default(20) }}
   OR issue_density_per_kloc >= {{ density_threshold | default(20) }}
ORDER BY (COALESCE(smell_density_per_kloc, 0) + COALESCE(issue_density_per_kloc, 0)) DESC
LIMIT {{ limit | default(50) }}
