-- Trust score trend: shows trust score for recent runs of the same repo
-- Returns up to 10 most recent runs ordered by date
SELECT
    cr.collection_run_id,
    cr.repo_id,
    cr.commit,
    cr.started_at,
    qs.trust_score,
    qs.tools_expected,
    qs.tools_completed,
    qs.tools_failed,
    qs.tools_empty,
    qs.warning_count
FROM lz_run_quality_summary qs
JOIN lz_collection_runs cr ON cr.collection_run_id = qs.collection_run_id
WHERE cr.repo_id = (
    SELECT cr2.repo_id
    FROM lz_tool_runs tr
    JOIN lz_collection_runs cr2 ON cr2.collection_run_id = tr.collection_run_id
    WHERE tr.run_pk = ?
    LIMIT 1
)
AND cr.status IN ('completed', 'partial_success')
ORDER BY cr.started_at DESC
LIMIT 10
