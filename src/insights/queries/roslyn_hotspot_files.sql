-- Files with most Roslyn violations for Caldera
-- Uses stg_roslyn_file_metrics (includes relative_path directly)

SELECT
    rfm.relative_path,
    rfm.violation_count,
    rfm.severity_critical AS critical,
    rfm.severity_high AS high,
    rfm.severity_medium AS medium,
    rfm.cat_security AS security,
    rfm.cat_design AS design,
    rfm.cat_resource AS resource,
    rfm.cat_dead_code AS dead_code,
    rfm.cat_performance AS performance
FROM stg_roslyn_file_metrics rfm
WHERE rfm.run_pk = {{ run_pk }}
  AND rfm.violation_count > 0
ORDER BY rfm.violation_count DESC
LIMIT {{ limit | default(15) }}
