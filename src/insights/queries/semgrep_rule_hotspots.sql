-- Code quality rules query
-- Uses mart_semgrep_rule_hotspots to show rule-level aggregates
-- Resolves semgrep run_pk from SCC's collection

WITH run_map AS (
    SELECT tr_semgrep.run_pk AS semgrep_run_pk
    FROM lz_tool_runs tr_scc
    LEFT JOIN lz_tool_runs tr_semgrep
        ON tr_semgrep.collection_run_id = tr_scc.collection_run_id
        AND tr_semgrep.tool_name = 'semgrep'
    WHERE tr_scc.run_pk = {{ run_pk }}
)
SELECT
    rule_id,
    dd_category,
    sample_message,
    smell_count,
    files_affected,
    directories_affected,
    severity_critical,
    severity_high,
    severity_medium,
    severity_low,
    severity_info,
    severity_high_plus,
    severity_score,
    smell_rank,
    severity_rank,
    spread_rank,
    risk_level
FROM mart_semgrep_rule_hotspots
WHERE run_pk = (SELECT semgrep_run_pk FROM run_map)
ORDER BY smell_count DESC, severity_score DESC
LIMIT {{ limit | default(30) }}
