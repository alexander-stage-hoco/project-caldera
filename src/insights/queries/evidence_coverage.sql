-- Evidence: coverage gaps
-- Finds files with coverage < 50% AND ccn > 15 from unified_file_metrics
-- Used by EvidenceCollector to populate coverage evidence items

WITH run_map AS (
    SELECT tr_scc.run_pk AS scc_run_pk
    FROM lz_tool_runs tr_scc
    WHERE tr_scc.run_pk = {{ run_pk }}
)
SELECT
    ufm.relative_path,
    ufm.loc_total,
    ufm.max_ccn,
    ufm.total_ccn,
    ufm.function_count,
    ufm.line_coverage_pct,
    ufm.branch_coverage_pct,
    (SELECT scc_run_pk FROM run_map) AS tool_run_pk
FROM unified_file_metrics ufm
WHERE ufm.run_pk = (SELECT scc_run_pk FROM run_map)
  AND ufm.line_coverage_pct IS NOT NULL
  AND ufm.line_coverage_pct < {{ coverage_threshold | default(50) }}
  AND ufm.max_ccn > {{ ccn_threshold | default(15) }}
ORDER BY ufm.max_ccn DESC, ufm.line_coverage_pct ASC
LIMIT {{ limit | default(50) }}
