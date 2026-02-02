-- Repository health overview query for Caldera
-- Combines unified_run_summary with repo_health_summary

SELECT
    COALESCE(urs.total_files, ufm.total_files) AS total_files,
    COALESCE(urs.total_loc, ufm.total_loc) AS total_loc,
    COALESCE(urs.total_code, ufm.total_code) AS total_code,
    COALESCE(urs.total_comment, ufm.total_comment) AS total_comment,
    COALESCE(urs.avg_ccn, ufm.avg_ccn) AS avg_ccn,
    COALESCE(urs.max_ccn, ufm.max_ccn) AS max_ccn,
    rhs.health_grade,
    rhs.violation_count,
    rhs.lfs_candidate_count
FROM (
    -- Fallback aggregation from unified_file_metrics
    SELECT
        COUNT(DISTINCT relative_path) AS total_files,
        SUM(loc_total) AS total_loc,
        SUM(loc_code) AS total_code,
        SUM(loc_comment) AS total_comment,
        AVG(complexity_total_ccn) AS avg_ccn,
        MAX(complexity_max) AS max_ccn
    FROM unified_file_metrics
    WHERE run_pk = {{ run_pk }}
) ufm
LEFT JOIN (
    SELECT *
    FROM unified_run_summary
    WHERE run_pk = {{ run_pk }}
) urs ON TRUE
LEFT JOIN (
    SELECT *
    FROM repo_health_summary
    WHERE run_pk = {{ run_pk }}
) rhs ON TRUE
