-- Git-sizer violation details for Caldera
-- Resolves git-sizer run_pk from any tool's collection

WITH run_map AS (
    SELECT tr_tool.run_pk AS git_sizer_run_pk
    FROM lz_tool_runs tr_source
    LEFT JOIN lz_tool_runs tr_tool
        ON tr_tool.collection_run_id = tr_source.collection_run_id
        AND tr_tool.tool_name = 'git-sizer'
    WHERE tr_source.run_pk = {{ run_pk }}
)
SELECT
    metric,
    violation_count,
    max_level,
    sample_value_display,
    sample_object_ref,
    level_3_plus,
    severity_score,
    risk_level
FROM mart_git_sizer_violation_hotspots
WHERE run_pk = (SELECT git_sizer_run_pk FROM run_map)
ORDER BY severity_score DESC
LIMIT {{ limit | default(20) }}
