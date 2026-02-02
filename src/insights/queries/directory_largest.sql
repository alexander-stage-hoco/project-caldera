-- Directory ranking by lines of code for Caldera
-- Uses pre-computed rollup_scc_directory_recursive_counts

SELECT
    rs.directory_path,
    rs.file_count,
    rs.total_lines,
    rs.total_code_lines AS total_code,
    rs.total_comment_lines AS total_comments,
    rs.total_complexity
FROM rollup_scc_directory_counts_recursive rs
WHERE rs.run_pk = {{ run_pk }}
  AND rs.total_lines > 0
ORDER BY rs.total_lines DESC
LIMIT {{ limit | default(15) }}
