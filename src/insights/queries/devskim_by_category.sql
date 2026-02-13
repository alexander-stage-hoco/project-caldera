-- DevSkim findings by security category for Caldera
-- Resolves devskim run_pk from any tool's collection

WITH run_map AS (
    SELECT tr_tool.run_pk AS devskim_run_pk
    FROM lz_tool_runs tr_source
    LEFT JOIN lz_tool_runs tr_tool
        ON tr_tool.collection_run_id = tr_source.collection_run_id
        AND tr_tool.tool_name = 'devskim'
    WHERE tr_source.run_pk = {{ run_pk }}
)
SELECT
    'SQL Injection' AS category,
    SUM(cat_sql_injection) AS count
FROM stg_devskim_file_metrics
WHERE run_pk = (SELECT devskim_run_pk FROM run_map)
HAVING count > 0

UNION ALL

SELECT
    'Hardcoded Secret' AS category,
    SUM(cat_hardcoded_secret) AS count
FROM stg_devskim_file_metrics
WHERE run_pk = (SELECT devskim_run_pk FROM run_map)
HAVING count > 0

UNION ALL

SELECT
    'Insecure Crypto' AS category,
    SUM(cat_insecure_crypto) AS count
FROM stg_devskim_file_metrics
WHERE run_pk = (SELECT devskim_run_pk FROM run_map)
HAVING count > 0

UNION ALL

SELECT
    'XSS' AS category,
    SUM(cat_xss) AS count
FROM stg_devskim_file_metrics
WHERE run_pk = (SELECT devskim_run_pk FROM run_map)
HAVING count > 0

UNION ALL

SELECT
    'Command Injection' AS category,
    SUM(cat_command_injection) AS count
FROM stg_devskim_file_metrics
WHERE run_pk = (SELECT devskim_run_pk FROM run_map)
HAVING count > 0

UNION ALL

SELECT
    'Path Traversal' AS category,
    SUM(cat_path_traversal) AS count
FROM stg_devskim_file_metrics
WHERE run_pk = (SELECT devskim_run_pk FROM run_map)
HAVING count > 0

UNION ALL

SELECT
    'Insecure Deserialization' AS category,
    SUM(cat_insecure_deserialization) AS count
FROM stg_devskim_file_metrics
WHERE run_pk = (SELECT devskim_run_pk FROM run_map)
HAVING count > 0

UNION ALL

SELECT
    'Insecure SSL/TLS' AS category,
    SUM(cat_insecure_ssl_tls) AS count
FROM stg_devskim_file_metrics
WHERE run_pk = (SELECT devskim_run_pk FROM run_map)
HAVING count > 0

UNION ALL

SELECT
    'Insecure Random' AS category,
    SUM(cat_insecure_random) AS count
FROM stg_devskim_file_metrics
WHERE run_pk = (SELECT devskim_run_pk FROM run_map)
HAVING count > 0

UNION ALL

SELECT
    'Insecure File Handling' AS category,
    SUM(cat_insecure_file_handling) AS count
FROM stg_devskim_file_metrics
WHERE run_pk = (SELECT devskim_run_pk FROM run_map)
HAVING count > 0

UNION ALL

SELECT
    'Information Disclosure' AS category,
    SUM(cat_information_disclosure) AS count
FROM stg_devskim_file_metrics
WHERE run_pk = (SELECT devskim_run_pk FROM run_map)
HAVING count > 0

UNION ALL

SELECT
    'Authentication' AS category,
    SUM(cat_authentication) AS count
FROM stg_devskim_file_metrics
WHERE run_pk = (SELECT devskim_run_pk FROM run_map)
HAVING count > 0

UNION ALL

SELECT
    'Authorization' AS category,
    SUM(cat_authorization) AS count
FROM stg_devskim_file_metrics
WHERE run_pk = (SELECT devskim_run_pk FROM run_map)
HAVING count > 0

UNION ALL

SELECT
    'XML Injection' AS category,
    SUM(cat_xml_injection) AS count
FROM stg_devskim_file_metrics
WHERE run_pk = (SELECT devskim_run_pk FROM run_map)
HAVING count > 0

ORDER BY count DESC
