-- Rewrite risk constraint detection per directory
-- Identifies where incremental modernisation breaks down:
--   1. Monolithic modules — high LOC Gini + high complexity + concentrated work
--   2. Tight coupling clusters — high aggregate coupling with high fan_out
--   3. Knowledge silos on critical paths — single-author files with high complexity + coupling
--   4. Untested core — high complexity with zero/low coverage
--
-- Each row is a directory-level constraint with classification and risk level.

WITH run_map AS (
    SELECT
        tr_scc.run_pk AS scc_run_pk,
        tr_lizard.run_pk AS lizard_run_pk,
        tr_blame.run_pk AS blame_run_pk
    FROM lz_tool_runs tr_scc
    LEFT JOIN lz_tool_runs tr_lizard
        ON tr_lizard.collection_run_id = tr_scc.collection_run_id
        AND tr_lizard.tool_name = 'lizard'
    LEFT JOIN lz_tool_runs tr_blame
        ON tr_blame.collection_run_id = tr_scc.collection_run_id
        AND tr_blame.tool_name = 'git-blame-scanner'
    WHERE tr_scc.tool_name = 'scc'
      AND tr_scc.run_pk = {{ run_pk }}
),

-- LOC distribution per directory (Gini, top_10_share)
scc_dist AS (
    SELECT
        directory_path,
        gini_value AS loc_gini,
        top_10_pct_share AS loc_top_10_share,
        value_count AS file_count
    FROM rollup_scc_directory_recursive_distributions
    WHERE run_pk = (SELECT scc_run_pk FROM run_map)
      AND metric = 'lines_total'
      AND value_count >= 3
),

-- Complexity distribution per directory
lizard_dist AS (
    SELECT
        directory_path,
        gini_value AS ccn_gini,
        avg_value AS avg_ccn,
        p90_value AS ccn_p90,
        max_value AS max_ccn
    FROM rollup_lizard_directory_recursive_distributions
    WHERE run_pk = (SELECT lizard_run_pk FROM run_map)
      AND metric = 'total_ccn'
      AND value_count >= 3
),

-- Directory-level aggregated metrics
dir_metrics AS (
    SELECT
        directory_path,
        loc_total,
        lizard_total_ccn,
        lizard_avg_ccn,
        coupling_fan_out,
        coupling_fan_in,
        coupling_outgoing_calls,
        coverage_line_pct,
        blame_single_author_files,
        blame_knowledge_silo_count,
        blame_high_concentration_files,
        file_count
    FROM unified_directory_metrics
    WHERE run_pk = (SELECT scc_run_pk FROM run_map)
      AND loc_total > 0
),

-- Blame-based knowledge risk aggregated per directory
blame_dir AS (
    SELECT
        directory_id,
        COUNT(*) AS total_files,
        SUM(CASE WHEN is_single_author THEN total_lines ELSE 0 END) AS single_author_loc,
        SUM(total_lines) AS total_loc,
        AVG(risk_score) AS avg_risk_score,
        MAX(risk_score) AS max_risk_score
    FROM mart_git_blame_knowledge_risk
    WHERE run_pk = (SELECT blame_run_pk FROM run_map)
    GROUP BY directory_id
),

-- Combine all signals per directory
combined AS (
    SELECT
        dm.directory_path,
        dm.loc_total,
        dm.file_count,
        dm.lizard_total_ccn,
        dm.lizard_avg_ccn,
        dm.coupling_fan_out,
        dm.coupling_fan_in,
        dm.coupling_outgoing_calls,
        dm.coverage_line_pct,
        dm.blame_single_author_files,
        dm.blame_knowledge_silo_count,

        COALESCE(sd.loc_gini, 0) AS loc_gini,
        COALESCE(sd.loc_top_10_share, 0) AS loc_top_10_share,
        COALESCE(ld.ccn_gini, 0) AS ccn_gini,
        COALESCE(ld.avg_ccn, 0) AS avg_ccn,
        COALESCE(ld.ccn_p90, 0) AS ccn_p90,
        COALESCE(ld.max_ccn, 0) AS max_ccn,

        COALESCE(bd.single_author_loc, 0) AS single_author_loc,
        COALESCE(bd.total_loc, 0) AS blame_total_loc,
        COALESCE(bd.avg_risk_score, 0) AS avg_risk_score,

        -- Signal flags
        -- S1: Monolithic module
        CASE WHEN COALESCE(sd.loc_gini, 0) > 0.7
              AND COALESCE(ld.avg_ccn, 0) > 5
              AND COALESCE(sd.loc_top_10_share, 0) > 0.6
            THEN 1 ELSE 0 END AS is_monolith,

        -- S2: Tight coupling cluster
        CASE WHEN COALESCE(dm.coupling_fan_out, 0) + COALESCE(dm.coupling_fan_in, 0) > 20
              AND COALESCE(dm.coupling_fan_out, 0) > COALESCE(dm.coupling_fan_in, 0) * 1.5
            THEN 1 ELSE 0 END AS is_tight_coupling,

        -- S2b: Bidirectional coupling (structural)
        CASE WHEN COALESCE(dm.coupling_fan_out, 0) + COALESCE(dm.coupling_fan_in, 0) > 20
              AND COALESCE(dm.coupling_fan_out, 0) <= COALESCE(dm.coupling_fan_in, 0) * 1.5
              AND COALESCE(dm.coupling_fan_in, 0) > 0
            THEN 1 ELSE 0 END AS is_bidirectional_coupling,

        -- S3: Knowledge silo on critical path
        CASE WHEN COALESCE(bd.single_author_loc, 0) > COALESCE(bd.total_loc, 1) * 0.5
              AND COALESCE(dm.lizard_total_ccn, 0) > 10
              AND COALESCE(dm.coupling_fan_out, 0) + COALESCE(dm.coupling_fan_in, 0) > 5
            THEN 1 ELSE 0 END AS is_knowledge_silo,

        -- S4: Untested core
        CASE WHEN COALESCE(dm.lizard_avg_ccn, 0) > 5
              AND COALESCE(dm.coverage_line_pct, 0) < 10
            THEN 1 ELSE 0 END AS is_untested_core

    FROM dir_metrics dm
    LEFT JOIN scc_dist sd ON sd.directory_path = dm.directory_path
    LEFT JOIN lizard_dist ld ON ld.directory_path = dm.directory_path
    LEFT JOIN unified_directory_metrics udm
        ON udm.directory_path = dm.directory_path
        AND udm.run_pk = (SELECT scc_run_pk FROM run_map)
    LEFT JOIN blame_dir bd ON bd.directory_id = udm.directory_id
),

-- Build constraint rows (one per detected signal per directory)
constraints AS (
    -- Monolithic modules
    SELECT
        directory_path,
        loc_total,
        file_count,
        'monolith' AS signal,
        CASE
            WHEN is_monolith = 1 AND (is_tight_coupling = 1 OR is_bidirectional_coupling = 1) AND is_knowledge_silo = 1
                THEN 'structural'
            WHEN is_monolith = 1 AND (is_tight_coupling = 1 OR is_bidirectional_coupling = 1)
                THEN 'structural'
            WHEN is_monolith = 1
                THEN 'structural'
            ELSE 'addressable'
        END AS constraint_type,
        CASE
            WHEN is_monolith = 1 AND (is_tight_coupling = 1 OR is_bidirectional_coupling = 1) AND is_knowledge_silo = 1
                THEN 'high'
            WHEN is_monolith = 1 AND (is_tight_coupling = 1 OR is_bidirectional_coupling = 1)
                THEN 'high'
            WHEN is_monolith = 1
                THEN 'medium'
            ELSE 'low'
        END AS risk_level,
        loc_gini,
        loc_top_10_share,
        avg_ccn,
        ccn_p90,
        coupling_fan_out,
        coupling_fan_in,
        coverage_line_pct,
        single_author_loc,
        blame_total_loc
    FROM combined
    WHERE is_monolith = 1

    UNION ALL

    -- Tight coupling clusters
    SELECT
        directory_path,
        loc_total,
        file_count,
        CASE WHEN is_bidirectional_coupling = 1 THEN 'bidirectional_coupling' ELSE 'unidirectional_coupling' END AS signal,
        CASE WHEN is_bidirectional_coupling = 1 THEN 'structural' ELSE 'addressable' END AS constraint_type,
        'medium' AS risk_level,
        loc_gini,
        loc_top_10_share,
        avg_ccn,
        ccn_p90,
        coupling_fan_out,
        coupling_fan_in,
        coverage_line_pct,
        single_author_loc,
        blame_total_loc
    FROM combined
    WHERE is_tight_coupling = 1 OR is_bidirectional_coupling = 1

    UNION ALL

    -- Knowledge silos on critical paths
    SELECT
        directory_path,
        loc_total,
        file_count,
        'knowledge_silo' AS signal,
        'addressable' AS constraint_type,
        'low' AS risk_level,
        loc_gini,
        loc_top_10_share,
        avg_ccn,
        ccn_p90,
        coupling_fan_out,
        coupling_fan_in,
        coverage_line_pct,
        single_author_loc,
        blame_total_loc
    FROM combined
    WHERE is_knowledge_silo = 1

    UNION ALL

    -- Untested core
    SELECT
        directory_path,
        loc_total,
        file_count,
        'untested_core' AS signal,
        'addressable' AS constraint_type,
        CASE WHEN loc_total > 3000 THEN 'high' WHEN loc_total > 2000 THEN 'medium' ELSE 'medium' END AS risk_level,
        loc_gini,
        loc_top_10_share,
        avg_ccn,
        ccn_p90,
        coupling_fan_out,
        coupling_fan_in,
        coverage_line_pct,
        single_author_loc,
        blame_total_loc
    FROM combined
    WHERE is_untested_core = 1
)

SELECT
    directory_path,
    loc_total,
    file_count,
    signal,
    constraint_type,
    risk_level,
    ROUND(loc_gini, 3) AS loc_gini,
    ROUND(loc_top_10_share * 100, 1) AS loc_top_10_pct,
    ROUND(avg_ccn, 1) AS avg_ccn,
    ROUND(ccn_p90, 1) AS ccn_p90,
    COALESCE(coupling_fan_out, 0) AS coupling_fan_out,
    COALESCE(coupling_fan_in, 0) AS coupling_fan_in,
    ROUND(COALESCE(coverage_line_pct, 0), 1) AS coverage_line_pct,
    single_author_loc,
    blame_total_loc
FROM constraints
ORDER BY
    CASE risk_level WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END,
    CASE constraint_type WHEN 'structural' THEN 1 ELSE 2 END,
    loc_total DESC
