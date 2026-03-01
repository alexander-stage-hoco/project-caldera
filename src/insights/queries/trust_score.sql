-- Trust score and quality summary for the current collection run
SELECT
    qs.trust_score,
    qs.tools_expected,
    qs.tools_completed,
    qs.tools_skipped,
    qs.tools_failed,
    qs.tools_empty,
    qs.ingestion_errors,
    qs.warning_count
FROM lz_run_quality_summary qs
JOIN lz_tool_runs tr ON tr.collection_run_id = qs.collection_run_id
WHERE tr.run_pk = ?
LIMIT 1
