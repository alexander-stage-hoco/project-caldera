-- File hotspots query for Caldera
-- Retrieves top files by complexity, LOC, or smell count
-- Uses unified_file_metrics joined with stg_semgrep_file_metrics and stg_lz_lizard_file_metrics
-- Use order_by parameter: 'complexity', 'loc', or 'smells'

SELECT
    ufm.relative_path,
    ufm.loc_total,
    ufm.complexity_total_ccn AS complexity,
    ufm.complexity_max AS max_ccn,
    COALESCE(sfm.smell_count, 0) AS smell_count,
    COALESCE(lzfm.function_count, 0) AS function_count,
    -- Fallback: derive language from file extension if not available
    COALESCE(
        lf.language,
        CASE
            WHEN ufm.relative_path LIKE '%.cs' THEN 'C#'
            WHEN ufm.relative_path LIKE '%.py' THEN 'Python'
            WHEN ufm.relative_path LIKE '%.js' THEN 'JavaScript'
            WHEN ufm.relative_path LIKE '%.ts' THEN 'TypeScript'
            WHEN ufm.relative_path LIKE '%.java' THEN 'Java'
            WHEN ufm.relative_path LIKE '%.go' THEN 'Go'
            WHEN ufm.relative_path LIKE '%.rs' THEN 'Rust'
            WHEN ufm.relative_path LIKE '%.cpp' OR ufm.relative_path LIKE '%.cc' THEN 'C++'
            WHEN ufm.relative_path LIKE '%.c' THEN 'C'
            WHEN ufm.relative_path LIKE '%.rb' THEN 'Ruby'
            WHEN ufm.relative_path LIKE '%.php' THEN 'PHP'
            WHEN ufm.relative_path LIKE '%.swift' THEN 'Swift'
            WHEN ufm.relative_path LIKE '%.kt' THEN 'Kotlin'
            WHEN ufm.relative_path LIKE '%.scala' THEN 'Scala'
            WHEN ufm.relative_path LIKE '%.xaml' THEN 'XAML'
            WHEN ufm.relative_path LIKE '%.sql' THEN 'SQL'
            WHEN ufm.relative_path LIKE '%.sh' THEN 'Shell'
            ELSE 'Other'
        END
    ) AS language
FROM unified_file_metrics ufm
LEFT JOIN stg_semgrep_file_metrics sfm
    ON ufm.semgrep_run_pk = sfm.run_pk AND ufm.file_id = sfm.file_id
LEFT JOIN stg_lz_layout_files lf
    ON ufm.layout_run_pk = lf.run_pk AND ufm.file_id = lf.file_id
LEFT JOIN stg_lz_lizard_file_metrics lzfm
    ON ufm.lizard_run_pk = lzfm.run_pk AND ufm.file_id = lzfm.file_id
WHERE ufm.run_pk = {{ run_pk }}
  AND ufm.complexity_total_ccn IS NOT NULL
ORDER BY
    CASE '{{ order_by | default("complexity") }}'
        WHEN 'complexity' THEN ufm.complexity_total_ccn
        WHEN 'loc' THEN ufm.loc_total
        WHEN 'smells' THEN COALESCE(sfm.smell_count, 0)
    END DESC
LIMIT {{ limit | default(20) }}
