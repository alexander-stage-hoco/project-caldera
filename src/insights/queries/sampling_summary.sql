-- Sampling summary: codebase coverage statistics
-- Shows total files/LOC and how many are eligible for sampling
-- Used by SamplingRationaleSection to contextualize the sample

SELECT
    COUNT(*) AS total_files,
    COALESCE(SUM(loc_total), 0) AS total_loc,
    COUNT(CASE WHEN loc_total > 50 THEN 1 END) AS eligible_files,
    COALESCE(SUM(CASE WHEN loc_total > 50 THEN loc_total ELSE 0 END), 0) AS eligible_loc
FROM unified_file_metrics
WHERE run_pk = {{ run_pk }}
