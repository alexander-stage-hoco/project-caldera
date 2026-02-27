-- Evidence: coverage gaps
-- Finds files with coverage < 50% AND complexity_max > 15 from unified_file_metrics
-- Used by EvidenceCollector to populate coverage evidence items

WITH run_map AS (
    SELECT tr_scc.run_pk AS scc_run_pk
    FROM lz_tool_runs tr_scc
    WHERE tr_scc.run_pk = {{ run_pk }}
)
SELECT
    ufm.relative_path,
    ufm.loc_total,
    ufm.complexity_max,
    ufm.complexity_total_ccn,
    ufm.function_count,
    ufm.coverage_line_pct,
    ufm.coverage_branch_pct,
    (SELECT scc_run_pk FROM run_map) AS tool_run_pk
FROM unified_file_metrics ufm
WHERE ufm.run_pk = (SELECT scc_run_pk FROM run_map)
  AND ufm.coverage_line_pct IS NOT NULL
  AND ufm.coverage_line_pct < {{ coverage_threshold | default(50) }}
  AND ufm.complexity_max > {{ ccn_threshold | default(15) }}
ORDER BY ufm.complexity_max DESC, ufm.coverage_line_pct ASC
LIMIT {{ limit | default(50) }}
