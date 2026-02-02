-- Concentration analysis - top 20% files by complexity for Caldera
-- Shows files that concentrate the most complexity

WITH ranked_files AS (
    SELECT
        ufm.relative_path,
        ufm.complexity_total_ccn,
        ufm.loc_total,
        PERCENT_RANK() OVER (ORDER BY ufm.complexity_total_ccn DESC) AS pct_rank
    FROM unified_file_metrics ufm
    WHERE ufm.run_pk = {{ run_pk }}
      AND ufm.complexity_total_ccn IS NOT NULL
      AND ufm.complexity_total_ccn > 0
)
SELECT
    relative_path,
    complexity_total_ccn AS complexity,
    loc_total AS loc,
    ROUND(pct_rank * 100, 1) AS percentile
FROM ranked_files
WHERE pct_rank <= 0.20
ORDER BY complexity_total_ccn DESC
LIMIT 20
