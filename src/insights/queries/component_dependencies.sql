-- Component dependencies query
-- Finds inter-component call relationships from symbol_calls
-- Groups by source/target component directories

WITH run_map AS (
    -- Resolve tool-specific run_pks from collection
    SELECT
        tr_layout.run_pk AS layout_run_pk,
        tr_symbol.run_pk AS symbol_run_pk
    FROM lz_tool_runs tr_scc
    LEFT JOIN lz_tool_runs tr_layout
        ON tr_layout.collection_run_id = tr_scc.collection_run_id
        AND tr_layout.tool_name IN ('layout', 'layout-scanner')
    LEFT JOIN lz_tool_runs tr_symbol
        ON tr_symbol.collection_run_id = tr_scc.collection_run_id
        AND tr_symbol.tool_name = 'symbol-scanner'
    WHERE tr_scc.tool_name = 'scc'
      AND tr_scc.run_pk = {{ run_pk }}
),
-- Get component directories (depth 1-2)
component_dirs AS (
    SELECT
        directory_id,
        relative_path,
        depth
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
),
-- Map files to their component directories
file_to_component AS (
    SELECT
        lf.file_id,
        lf.relative_path AS file_path,
        cd.directory_id AS component_id,
        cd.relative_path AS component_path
    FROM lz_layout_files lf
    JOIN run_map rm ON rm.layout_run_pk = lf.run_pk
    JOIN component_dirs cd ON cd.directory_id = lf.directory_id
       OR lf.relative_path LIKE cd.relative_path || '/%'
),
-- Find calls between different components
inter_component_calls AS (
    SELECT
        sc.caller_file_id,
        sc.callee_file_id,
        sc.caller_symbol,
        sc.callee_symbol,
        sc.call_type,
        fc_caller.component_id AS source_component_id,
        fc_caller.component_path AS source_component,
        fc_callee.component_id AS target_component_id,
        fc_callee.component_path AS target_component
    FROM lz_symbol_calls sc
    JOIN run_map rm ON TRUE
    JOIN file_to_component fc_caller
        ON fc_caller.file_id = sc.caller_file_id
    LEFT JOIN file_to_component fc_callee
        ON fc_callee.file_id = sc.callee_file_id
    WHERE sc.run_pk = (SELECT symbol_run_pk FROM run_map)
      -- Only inter-component calls (different components)
      AND (fc_callee.component_id IS NULL
           OR fc_caller.component_id != fc_callee.component_id)
),
-- Aggregate outbound dependencies
outbound AS (
    SELECT
        source_component_id,
        source_component,
        target_component,
        COALESCE(call_type, 'direct') AS call_type,
        COUNT(*) AS call_count,
        COUNT(DISTINCT caller_symbol) AS unique_callers,
        COUNT(DISTINCT callee_symbol) AS unique_callees
    FROM inter_component_calls
    WHERE target_component IS NOT NULL
    GROUP BY source_component_id, source_component, target_component, call_type
),
-- Aggregate inbound dependencies
inbound AS (
    SELECT
        target_component_id,
        target_component,
        source_component,
        COALESCE(call_type, 'direct') AS call_type,
        COUNT(*) AS call_count,
        COUNT(DISTINCT caller_symbol) AS unique_callers,
        COUNT(DISTINCT callee_symbol) AS unique_callees
    FROM inter_component_calls
    WHERE target_component IS NOT NULL
    GROUP BY target_component_id, target_component, source_component, call_type
)
-- Return both outbound and inbound as separate result sets
-- Using UNION to combine with direction indicator
SELECT
    'outbound' AS direction,
    source_component_id AS component_id,
    source_component AS component_path,
    target_component AS related_component,
    call_type,
    call_count,
    unique_callers,
    unique_callees
FROM outbound

UNION ALL

SELECT
    'inbound' AS direction,
    target_component_id AS component_id,
    target_component AS component_path,
    source_component AS related_component,
    call_type,
    call_count,
    unique_callers,
    unique_callees
FROM inbound

ORDER BY component_path, direction, call_count DESC
