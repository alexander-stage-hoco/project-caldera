-- Code size hotspots query
-- Uses mart_scc_size_hotspots to identify large/complex files
-- SCC is the anchor tool so run_pk is used directly

SELECT
    relative_path,
    language,
    lines_total,
    code_lines,
    comment_lines,
    blank_lines,
    complexity,
    complexity_density,
    comment_ratio,
    code_ratio,
    risk_level,
    risk_level_numeric,
    relative_position,
    lines_zscore,
    complexity_zscore,
    lines_rank,
    is_critical,
    is_high_plus,
    run_lines_avg,
    run_lines_stddev,
    run_lines_p50,
    run_lines_p75,
    run_lines_p90,
    run_lines_p95,
    run_lines_p99,
    run_total_files
FROM mart_scc_size_hotspots
WHERE run_pk = {{ run_pk }}
ORDER BY lines_total DESC, complexity DESC
LIMIT {{ limit | default(30) }}
