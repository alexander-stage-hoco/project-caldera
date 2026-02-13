-- Dotcover assembly-level coverage for Caldera
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
    assembly_name,
    covered_statements,
    total_statements,
    statement_coverage_pct
FROM stg_lz_dotcover_assembly_coverage
WHERE run_pk = (SELECT dotcover_run_pk FROM run_map)
ORDER BY statement_coverage_pct ASC
LIMIT {{ limit | default(20) }}
