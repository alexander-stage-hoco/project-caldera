-- Claim support: complexity concentration (Gini stats)
-- Used by ComplexityConcentrationRule to detect concentrated complexity

WITH run_map AS (
    SELECT
        tr_scc.run_pk AS scc_run_pk,
        tr_lizard.run_pk AS lizard_run_pk
    FROM lz_tool_runs tr_scc
    LEFT JOIN lz_tool_runs tr_lizard
        ON tr_lizard.collection_run_id = tr_scc.collection_run_id
        AND tr_lizard.tool_name = 'lizard'
    WHERE tr_scc.run_pk = {{ run_pk }}
),
dir_stats AS (
    SELECT
        -- Extract top-level directory
        CASE
            WHEN POSITION('/' IN ufm.relative_path) > 0
            THEN SPLIT_PART(ufm.relative_path, '/', 1)
            ELSE '.'
        END AS directory_path,
        COUNT(*) AS file_count,
        SUM(ufm.complexity_total_ccn) AS complexity_total_ccn,
        MAX(ufm.complexity_max) AS complexity_max,
        AVG(ufm.complexity_total_ccn) AS avg_ccn
    FROM unified_file_metrics ufm
    WHERE ufm.run_pk = (SELECT scc_run_pk FROM run_map)
      AND ufm.function_count > 0
    GROUP BY 1
    HAVING COUNT(*) >= {{ min_files | default(10) }}
),
-- Calculate Gini coefficient per directory using ordered values
ranked AS (
    SELECT
        ds.directory_path,
        ds.file_count,
        ds.complexity_total_ccn,
        ds.complexity_max,
        ds.avg_ccn,
        ufm.relative_path,
        ufm.complexity_total_ccn AS file_ccn,
        ROW_NUMBER() OVER (PARTITION BY ds.directory_path ORDER BY ufm.complexity_total_ccn) AS rn
    FROM dir_stats ds
    JOIN unified_file_metrics ufm
        ON CASE
            WHEN POSITION('/' IN ufm.relative_path) > 0
            THEN SPLIT_PART(ufm.relative_path, '/', 1)
            ELSE '.'
           END = ds.directory_path
    WHERE ufm.run_pk = (SELECT scc_run_pk FROM run_map)
      AND ufm.function_count > 0
),
gini_calc AS (
    SELECT
        directory_path,
        file_count,
        complexity_total_ccn,
        complexity_max,
        avg_ccn,
        -- Gini formula: (2 * sum(i * xi)) / (n * sum(xi)) - (n + 1) / n
        CASE
            WHEN SUM(file_ccn) > 0
            THEN ROUND(
                (2.0 * SUM(rn * file_ccn)) / (file_count * SUM(file_ccn))
                - (file_count + 1.0) / file_count,
                3
            )
            ELSE 0
        END AS gini_ccn
    FROM ranked
    GROUP BY directory_path, file_count, complexity_total_ccn, complexity_max, avg_ccn
)
SELECT
    directory_path,
    file_count,
    complexity_total_ccn,
    complexity_max,
    ROUND(avg_ccn, 1) AS avg_ccn,
    gini_ccn
FROM gini_calc
WHERE gini_ccn > {{ gini_threshold | default(0.7) }}
ORDER BY gini_ccn DESC
