-- Top Roslyn violations by count for Caldera
-- Uses lz_roslyn_violations

SELECT
    rule_id,
    severity,
    category,
    COUNT(*) AS count,
    COUNT(DISTINCT file_id) AS affected_files
FROM lz_roslyn_violations
WHERE run_pk = {{ run_pk }}
GROUP BY rule_id, severity, category
ORDER BY
    CASE severity
        WHEN 'Error' THEN 1
        WHEN 'Warning' THEN 2
        WHEN 'Info' THEN 3
        ELSE 4
    END,
    count DESC
LIMIT {{ limit | default(20) }}
