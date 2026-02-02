-- Roslyn violations by category for Caldera
-- Uses stg_roslyn_file_metrics categories

SELECT
    'Security' AS category,
    SUM(cat_security) AS count
FROM stg_roslyn_file_metrics
WHERE run_pk = {{ run_pk }}
HAVING count > 0

UNION ALL

SELECT
    'Design' AS category,
    SUM(cat_design) AS count
FROM stg_roslyn_file_metrics
WHERE run_pk = {{ run_pk }}
HAVING count > 0

UNION ALL

SELECT
    'Resource' AS category,
    SUM(cat_resource) AS count
FROM stg_roslyn_file_metrics
WHERE run_pk = {{ run_pk }}
HAVING count > 0

UNION ALL

SELECT
    'Dead Code' AS category,
    SUM(cat_dead_code) AS count
FROM stg_roslyn_file_metrics
WHERE run_pk = {{ run_pk }}
HAVING count > 0

UNION ALL

SELECT
    'Performance' AS category,
    SUM(cat_performance) AS count
FROM stg_roslyn_file_metrics
WHERE run_pk = {{ run_pk }}
HAVING count > 0

ORDER BY count DESC
