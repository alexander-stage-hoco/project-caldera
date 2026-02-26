-- Sampling targets: composite risk score per file
-- Combines complexity, coupling, ownership, coverage, and quality signals
-- Used by SamplingRationaleSection to show top files and rationale

WITH run_map AS (
    SELECT
        tr_scc.run_pk AS scc_run_pk,
        tr_lizard.run_pk AS lizard_run_pk,
        tr_symbol.run_pk AS symbol_run_pk,
        tr_blame.run_pk AS blame_run_pk
    FROM lz_tool_runs tr_scc
    LEFT JOIN lz_tool_runs tr_lizard
        ON tr_lizard.collection_run_id = tr_scc.collection_run_id
        AND tr_lizard.tool_name = 'lizard'
    LEFT JOIN lz_tool_runs tr_symbol
        ON tr_symbol.collection_run_id = tr_scc.collection_run_id
        AND tr_symbol.tool_name = 'symbol-scanner'
    LEFT JOIN lz_tool_runs tr_blame
        ON tr_blame.collection_run_id = tr_scc.collection_run_id
        AND tr_blame.tool_name = 'git-blame-scanner'
    WHERE tr_scc.run_pk = {{ run_pk }}
),
base_files AS (
    SELECT
        ufm.relative_path,
        ufm.loc_total,
        ufm.complexity_max,
        ufm.complexity_total_ccn,
        ufm.function_count,
        COALESCE(ufm.semgrep_smell_count, 0) AS smell_count,
        COALESCE(ufm.sonarqube_issue_count, 0) + COALESCE(ufm.devskim_issue_count, 0) AS issue_count,
        ufm.coverage_line_pct,
        ufm.total_coupling
    FROM unified_file_metrics ufm
    WHERE ufm.run_pk = (SELECT scc_run_pk FROM run_map)
      AND ufm.loc_total > 50
),
blame_files AS (
    SELECT
        relative_path,
        risk_score,
        churn_30d,
        unique_authors,
        top_author_pct
    FROM mart_git_blame_knowledge_risk
    WHERE run_pk = (SELECT blame_run_pk FROM run_map)
),
-- Normalize scores to 0-1 range using percentile-based approach
stats AS (
    SELECT
        PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY complexity_max) AS ccn_p90,
        PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY smell_count + issue_count) AS quality_p90,
        PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY total_coupling) AS coupling_p90
    FROM base_files
    WHERE function_count > 0
),
scored AS (
    SELECT
        bf.relative_path,
        bf.loc_total,
        bf.complexity_max,
        bf.coverage_line_pct,
        bf.total_coupling,
        bl.unique_authors,
        bl.top_author_pct,
        bl.churn_30d,
        -- Complexity score (0-1)
        LEAST(1.0, COALESCE(bf.complexity_max * 1.0 / NULLIF(s.ccn_p90, 0), 0)) AS ccn_score,
        -- Coupling score (0-1, normalized against p90)
        LEAST(1.0, COALESCE(bf.total_coupling * 1.0 / NULLIF(s.coupling_p90, 0), 0)) AS coupling_score,
        -- Ownership score (0-1, from blame risk_score 0-100 + churn boost)
        LEAST(1.0, COALESCE(bl.risk_score / 100.0, 0) +
            CASE WHEN bl.churn_30d > 0 THEN 0.1 ELSE 0 END) AS ownership_score,
        -- Coverage score (inverted: low coverage = high score)
        CASE
            WHEN bf.coverage_line_pct IS NULL THEN 0.5
            ELSE LEAST(1.0, (100.0 - bf.coverage_line_pct) / 100.0)
        END AS coverage_score,
        -- Quality score
        LEAST(1.0, COALESCE((bf.smell_count + bf.issue_count) * 1.0 / NULLIF(s.quality_p90, 0), 0)) AS quality_score
    FROM base_files bf
    CROSS JOIN stats s
    LEFT JOIN blame_files bl ON bl.relative_path = bf.relative_path
),
composite AS (
    SELECT
        relative_path,
        loc_total,
        complexity_max,
        coverage_line_pct,
        total_coupling,
        unique_authors,
        top_author_pct,
        churn_30d,
        ccn_score,
        coupling_score,
        ownership_score,
        coverage_score,
        quality_score,
        ROUND(
            0.30 * ccn_score +
            0.25 * coupling_score +
            0.20 * ownership_score +
            0.15 * coverage_score +
            0.10 * quality_score,
            3
        ) AS composite_score
    FROM scored
)
SELECT *
FROM composite
WHERE composite_score > 0.1
ORDER BY composite_score DESC
LIMIT {{ limit | default(30) }}
