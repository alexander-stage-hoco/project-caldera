-- Language summary (top languages) for Caldera
-- Uses stg_lz_scc_file_metrics which has language column

SELECT
    scc.language,
    COUNT(*) AS file_count,
    SUM(scc.lines_total) AS loc
FROM stg_lz_scc_file_metrics scc
WHERE scc.run_pk = {{ run_pk }}
  AND scc.language IS NOT NULL
  AND scc.language != ''
GROUP BY scc.language
ORDER BY SUM(scc.lines_total) DESC
LIMIT {{ limit | default(10) }}
