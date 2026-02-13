-- Dotcover overall coverage summary for Caldera
-- Resolves dotcover run_pk from any tool's collection

WITH run_map AS (
    SELECT tr_tool.run_pk AS dotcover_run_pk
    FROM lz_tool_runs tr_source
    LEFT JOIN lz_tool_runs tr_tool
        ON tr_tool.collection_run_id = tr_source.collection_run_id
        AND tr_tool.tool_name = 'dotcover'
    WHERE tr_source.run_pk = {{ run_pk }}
)
SELECT
    COUNT(*) AS assembly_count,
    SUM(covered_statements) AS total_covered,
    SUM(total_statements) AS total_statements,
    ROUND(SUM(covered_statements)::FLOAT / NULLIF(SUM(total_statements), 0) * 100, 1) AS overall_coverage_pct
FROM stg_lz_dotcover_assembly_coverage
WHERE run_pk = (SELECT dotcover_run_pk FROM run_map)
