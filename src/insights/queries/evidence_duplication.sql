-- Evidence: code duplication blocks from PMD-CPD data

SELECT
    cpd.source_file AS relative_path,
    cpd.tokens,
    cpd.lines,
    cpd.occurrences,
    cpd.run_pk AS tool_run_pk
FROM stg_lz_pmd_cpd_duplications cpd
JOIN lz_tool_runs tr ON tr.run_pk = cpd.run_pk AND tr.tool_name = 'pmd-cpd'
WHERE tr.collection_run_id = (
    SELECT collection_run_id FROM lz_tool_runs WHERE run_pk = {{ run_pk }}
)
ORDER BY cpd.tokens DESC
LIMIT {{ limit | default(50) }}
