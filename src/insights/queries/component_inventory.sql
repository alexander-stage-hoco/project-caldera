-- Component inventory query
-- Identifies depth 1-2 directories as logical components with aggregated metrics
-- Combines size (SCC), complexity (Lizard), and coupling (symbol-scanner) data

WITH run_map AS (
    -- Resolve tool-specific run_pks from collection
    SELECT
        tr_scc.run_pk AS scc_run_pk,
        tr_layout.run_pk AS layout_run_pk,
        tr_lizard.run_pk AS lizard_run_pk,
        tr_symbol.run_pk AS symbol_run_pk,
        tr_blame.run_pk AS blame_run_pk
    FROM lz_tool_runs tr_scc
    LEFT JOIN lz_tool_runs tr_layout
        ON tr_layout.collection_run_id = tr_scc.collection_run_id
        AND tr_layout.tool_name IN ('layout', 'layout-scanner')
    LEFT JOIN lz_tool_runs tr_lizard
        ON tr_lizard.collection_run_id = tr_scc.collection_run_id
        AND tr_lizard.tool_name = 'lizard'
    LEFT JOIN lz_tool_runs tr_symbol
        ON tr_symbol.collection_run_id = tr_scc.collection_run_id
        AND tr_symbol.tool_name = 'symbol-scanner'
    LEFT JOIN lz_tool_runs tr_blame
        ON tr_blame.collection_run_id = tr_scc.collection_run_id
        AND tr_blame.tool_name = 'git-blame-scanner'
    WHERE tr_scc.tool_name = 'scc'
      AND tr_scc.run_pk = {{ run_pk }}
),
-- Identify components: depth 1-2 directories with code files
-- Filter out common non-component directories
components AS (
    SELECT
        ld.directory_id,
        ld.relative_path,
        ld.depth,
        ld.file_count
    FROM lz_layout_directories ld
    JOIN run_map rm ON rm.layout_run_pk = ld.run_pk
    WHERE ld.depth BETWEEN 1 AND 2
      AND ld.file_count > 0
      -- Filter out non-code directories
      AND ld.relative_path NOT LIKE 'test%'
      AND ld.relative_path NOT LIKE 'tests%'
      AND ld.relative_path NOT LIKE '%/test%'
      AND ld.relative_path NOT LIKE '%/tests%'
      AND ld.relative_path NOT LIKE 'docs%'
      AND ld.relative_path NOT LIKE 'doc%'
      AND ld.relative_path NOT LIKE '.%'
      AND ld.relative_path NOT LIKE 'node_modules%'
      AND ld.relative_path NOT LIKE 'vendor%'
      AND ld.relative_path NOT LIKE 'packages%'
      AND ld.relative_path NOT LIKE 'bin%'
      AND ld.relative_path NOT LIKE 'obj%'
),
-- Size metrics from SCC rollup (recursive)
scc_metrics AS (
    SELECT
        directory_id,
        directory_path,
        file_count,
        total_lines AS loc,
        total_code_lines AS code_loc,
        total_complexity AS complexity,
        language_count
    FROM rollup_scc_directory_counts_recursive
    WHERE run_pk = (SELECT scc_run_pk FROM run_map)
),
-- Complexity metrics from Lizard rollup (recursive)
lizard_metrics AS (
    SELECT
        directory_id,
        file_count AS lizard_file_count,
        total_function_count AS function_count,
        total_ccn,
        avg_ccn,
        max_ccn
    FROM rollup_lizard_directory_counts_recursive
    WHERE run_pk = (SELECT lizard_run_pk FROM run_map)
),
-- Coupling metrics: aggregate fan-in/fan-out per component directory
-- Using symbol_calls to compute directory-level coupling
coupling_by_dir AS (
    SELECT
        caller_directory_id AS directory_id,
        COUNT(DISTINCT callee_symbol) AS fan_out,
        COUNT(*) AS outbound_calls
    FROM lz_symbol_calls
    WHERE run_pk = (SELECT symbol_run_pk FROM run_map)
    GROUP BY caller_directory_id
),
coupling_in_by_dir AS (
    SELECT
        cs.callee_file_id,
        lf.directory_id,
        COUNT(DISTINCT cs.caller_symbol) AS fan_in,
        COUNT(*) AS inbound_calls
    FROM lz_symbol_calls cs
    JOIN run_map rm ON TRUE
    JOIN lz_layout_files lf
        ON lf.run_pk = rm.layout_run_pk
        AND lf.file_id = cs.callee_file_id
    WHERE cs.run_pk = (SELECT symbol_run_pk FROM run_map)
      AND cs.callee_file_id IS NOT NULL
    GROUP BY cs.callee_file_id, lf.directory_id
),
coupling_in_agg AS (
    SELECT
        directory_id,
        SUM(fan_in) AS fan_in,
        SUM(inbound_calls) AS inbound_calls
    FROM coupling_in_by_dir
    GROUP BY directory_id
),
-- Knowledge concentration from git-blame (when available)
blame_by_dir AS (
    SELECT
        directory_id,
        COUNT(DISTINCT file_id) AS blamed_files,
        AVG(top_author_pct) AS avg_top_author_pct,
        MAX(top_author_pct) AS max_top_author_pct,
        AVG(unique_authors) AS avg_unique_authors
    FROM lz_git_blame_summary
    WHERE run_pk = (SELECT blame_run_pk FROM run_map)
    GROUP BY directory_id
),
-- Combine all metrics
combined AS (
    SELECT
        c.directory_id,
        c.relative_path AS directory_path,
        c.depth,
        -- Size metrics
        COALESCE(s.file_count, c.file_count) AS file_count,
        COALESCE(s.loc, 0) AS loc,
        COALESCE(s.code_loc, 0) AS code_loc,
        COALESCE(s.complexity, 0) AS complexity,
        COALESCE(s.language_count, 0) AS language_count,
        -- Complexity metrics
        COALESCE(l.function_count, 0) AS function_count,
        COALESCE(l.total_ccn, 0) AS total_ccn,
        COALESCE(l.avg_ccn, 0) AS avg_ccn,
        COALESCE(l.max_ccn, 0) AS max_ccn,
        -- Coupling metrics
        COALESCE(co.fan_out, 0) AS fan_out,
        COALESCE(ci.fan_in, 0) AS fan_in,
        COALESCE(co.fan_out, 0) + COALESCE(ci.fan_in, 0) AS total_coupling,
        CASE
            WHEN COALESCE(co.fan_out, 0) + COALESCE(ci.fan_in, 0) = 0 THEN 0.5
            ELSE CAST(COALESCE(co.fan_out, 0) AS DOUBLE) /
                 (COALESCE(co.fan_out, 0) + COALESCE(ci.fan_in, 0))
        END AS instability,
        -- Knowledge metrics
        COALESCE(b.avg_top_author_pct, 0) AS avg_top_author_pct,
        COALESCE(b.max_top_author_pct, 0) AS max_top_author_pct,
        COALESCE(b.avg_unique_authors, 0) AS avg_unique_authors
    FROM components c
    LEFT JOIN scc_metrics s ON s.directory_id = c.directory_id
    LEFT JOIN lizard_metrics l ON l.directory_id = c.directory_id
    LEFT JOIN coupling_by_dir co ON co.directory_id = c.directory_id
    LEFT JOIN coupling_in_agg ci ON ci.directory_id = c.directory_id
    LEFT JOIN blame_by_dir b ON b.directory_id = c.directory_id
),
-- Calculate health score using weighted components
-- Reusing the module_health scoring pattern
scored AS (
    SELECT
        *,
        -- Component scores (normalized 0-1, higher = healthier)
        -- Complexity: Lower avg CCN is healthier (cap at 20)
        GREATEST(0, 1 - LEAST(avg_ccn, 20) / 20) AS complexity_score,
        -- Coupling: Lower total coupling is healthier (cap at 100)
        GREATEST(0, 1 - LEAST(total_coupling, 100) / 100) AS coupling_score,
        -- Instability: Prefer balanced (0.5 is ideal, penalize extremes)
        1 - ABS(instability - 0.5) * 2 AS stability_score,
        -- Knowledge: Lower concentration is healthier
        GREATEST(0, 1 - avg_top_author_pct / 100) AS knowledge_score,
        -- Size: Moderate size is healthy (penalize very large components)
        CASE
            WHEN loc <= 5000 THEN 1.0
            WHEN loc <= 10000 THEN 0.8
            WHEN loc <= 20000 THEN 0.6
            ELSE 0.4
        END AS size_score
    FROM combined
),
health_scored AS (
    SELECT
        *,
        -- Weighted health score (0-100)
        ROUND(100 * (
            0.30 * complexity_score +
            0.25 * coupling_score +
            0.15 * stability_score +
            0.15 * knowledge_score +
            0.15 * size_score
        ), 1) AS health_score
    FROM scored
)
SELECT
    directory_id,
    directory_path,
    -- Extract display name from path (last segment)
    CASE
        WHEN directory_path LIKE '%/%'
        THEN SPLIT_PART(directory_path, '/', -1)
        ELSE directory_path
    END AS display_name,
    depth,
    file_count,
    loc,
    code_loc,
    complexity,
    language_count,
    function_count,
    total_ccn,
    ROUND(avg_ccn, 1) AS avg_ccn,
    max_ccn,
    fan_in,
    fan_out,
    total_coupling,
    ROUND(instability, 2) AS instability,
    ROUND(avg_top_author_pct, 1) AS avg_top_author_pct,
    ROUND(max_top_author_pct, 1) AS max_top_author_pct,
    ROUND(avg_unique_authors, 1) AS avg_unique_authors,
    health_score,
    CASE
        WHEN health_score >= 90 THEN 'A'
        WHEN health_score >= 80 THEN 'B'
        WHEN health_score >= 70 THEN 'C'
        WHEN health_score >= 60 THEN 'D'
        ELSE 'F'
    END AS health_grade,
    -- Component scores for transparency
    ROUND(complexity_score * 100, 1) AS complexity_component,
    ROUND(coupling_score * 100, 1) AS coupling_component,
    ROUND(stability_score * 100, 1) AS stability_component,
    ROUND(knowledge_score * 100, 1) AS knowledge_component,
    ROUND(size_score * 100, 1) AS size_component
FROM health_scored
WHERE file_count > 0
ORDER BY health_score ASC, directory_path
