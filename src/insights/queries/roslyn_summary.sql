-- Roslyn violations summary by severity for Caldera
-- Uses stg_roslyn_file_metrics

SELECT
    'Critical' AS severity,
    SUM(severity_critical) AS count
FROM stg_roslyn_file_metrics
WHERE run_pk = {{ run_pk }}
HAVING count > 0

UNION ALL

SELECT
    'High' AS severity,
    SUM(severity_high) AS count
FROM stg_roslyn_file_metrics
WHERE run_pk = {{ run_pk }}
HAVING count > 0

UNION ALL

SELECT
    'Medium' AS severity,
    SUM(severity_medium) AS count
FROM stg_roslyn_file_metrics
WHERE run_pk = {{ run_pk }}
HAVING count > 0

UNION ALL

SELECT
    'Low' AS severity,
    SUM(severity_low) AS count
FROM stg_roslyn_file_metrics
WHERE run_pk = {{ run_pk }}
HAVING count > 0

UNION ALL

SELECT
    'Info' AS severity,
    SUM(severity_info) AS count
FROM stg_roslyn_file_metrics
WHERE run_pk = {{ run_pk }}
HAVING count > 0

ORDER BY
    CASE severity
        WHEN 'Critical' THEN 1
        WHEN 'High' THEN 2
        WHEN 'Medium' THEN 3
        WHEN 'Low' THEN 4
        WHEN 'Info' THEN 5
    END
