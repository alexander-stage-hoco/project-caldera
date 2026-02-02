-- Language coverage breakdown for Caldera
-- Uses stg_lz_scc_file_metrics for language, LOC, and comments
-- Joins with stg_lz_lizard_file_metrics for complexity via run_pk mapping

WITH run_map AS (
    -- Map scc run_pk to lizard run_pk within the same collection
    SELECT
        tr_scc.run_pk AS scc_run_pk,
        tr_lizard.run_pk AS lizard_run_pk
    FROM lz_tool_runs tr_scc
    LEFT JOIN lz_tool_runs tr_lizard
        ON tr_lizard.collection_run_id = tr_scc.collection_run_id
        AND tr_lizard.tool_name = 'lizard'
    WHERE tr_scc.tool_name = 'scc'
      AND tr_scc.run_pk = {{ run_pk }}
)
SELECT
    scc.language,
    COUNT(*) AS file_count,
    SUM(scc.lines_total) AS loc,
    SUM(scc.code_lines) AS code_lines,
    SUM(scc.comment_lines) AS comment_lines,
    AVG(lz.total_ccn) AS avg_complexity
FROM stg_lz_scc_file_metrics scc
LEFT JOIN run_map rm ON rm.scc_run_pk = scc.run_pk
LEFT JOIN stg_lz_lizard_file_metrics lz
    ON rm.lizard_run_pk = lz.run_pk AND scc.file_id = lz.file_id
WHERE scc.run_pk = {{ run_pk }}
  AND scc.language IS NOT NULL
  AND scc.language != ''
GROUP BY scc.language
ORDER BY SUM(scc.lines_total) DESC
