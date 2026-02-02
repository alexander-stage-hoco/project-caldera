-- Files that are both complex AND have code smells for Caldera
-- Uses unified_file_metrics joined with stg_semgrep_file_metrics

SELECT
    ufm.relative_path,
    ufm.complexity_total_ccn AS complexity,
    ufm.loc_total AS loc,
    sfm.smell_count,
    lf.language
FROM unified_file_metrics ufm
INNER JOIN stg_semgrep_file_metrics sfm
    ON ufm.semgrep_run_pk = sfm.run_pk AND ufm.file_id = sfm.file_id
    AND sfm.smell_count >= 3
LEFT JOIN stg_lz_layout_files lf
    ON ufm.layout_run_pk = lf.run_pk AND ufm.file_id = lf.file_id
WHERE ufm.run_pk = {{ run_pk }}
  AND ufm.complexity_total_ccn >= 10
ORDER BY (ufm.complexity_total_ccn * sfm.smell_count) DESC
LIMIT {{ limit | default(15) }}
