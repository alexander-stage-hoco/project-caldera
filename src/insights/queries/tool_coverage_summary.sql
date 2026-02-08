-- Tool coverage summary for a collection run
-- Shows which tools ran and how many files each analyzed
-- Parameters: run_pk (any tool's run_pk for the collection)

WITH collection AS (
    -- Get the collection_run_id from the given run_pk
    SELECT collection_run_id
    FROM lz_tool_runs
    WHERE run_pk = {{ run_pk }}
),
all_tools AS (
    -- List of expected tools (16 total)
    SELECT unnest([
        'layout-scanner', 'scc', 'lizard', 'semgrep', 'roslyn-analyzers',
        'sonarqube', 'trivy', 'gitleaks', 'symbol-scanner', 'scancode',
        'pmd-cpd', 'devskim', 'dotcover', 'git-fame', 'git-sizer', 'dependensee'
    ]) AS tool_name
),
tool_runs AS (
    -- Get all tool runs for this collection
    SELECT
        tr.tool_name,
        tr.run_pk,
        tr.tool_version,
        tr.schema_version,
        tr.timestamp
    FROM lz_tool_runs tr
    JOIN collection c ON tr.collection_run_id = c.collection_run_id
),
file_counts AS (
    -- Count distinct files analyzed per tool from unified_file_metrics sources column
    SELECT
        tr.tool_name,
        COUNT(DISTINCT fm.file_id) AS files_analyzed
    FROM tool_runs tr
    LEFT JOIN unified_file_metrics fm
        ON fm.sources LIKE '%' || tr.tool_name || '%'
        AND fm.collection_run_id = (SELECT collection_run_id FROM collection)
    GROUP BY tr.tool_name
)
SELECT
    expected.tool_name,
    CASE WHEN tr.run_pk IS NOT NULL THEN 'ran' ELSE 'missing' END AS status,
    tr.run_pk,
    tr.tool_version,
    tr.schema_version,
    tr.timestamp,
    COALESCE(fc.files_analyzed, 0) AS files_analyzed
FROM all_tools expected
LEFT JOIN tool_runs tr ON expected.tool_name = tr.tool_name
LEFT JOIN file_counts fc ON expected.tool_name = fc.tool_name
ORDER BY expected.tool_name
