-- Evidence: file size hotspots from SCC data
-- Files exceeding LOC threshold, ordered by size descending

SELECT
    ufm.relative_path,
    ufm.loc_total,
    ufm.language
FROM unified_file_metrics ufm
WHERE ufm.run_pk = {{ run_pk }}
  AND ufm.loc_total >= {{ loc_threshold | default(500) }}
ORDER BY ufm.loc_total DESC
LIMIT {{ limit | default(50) }}
