-- Coverage-ingest line counts per directory (direct - only files in that directory)

{{ calculate_count_stats(
    tool_name='coverage-ingest',
    scope='direct',
    staging_model='stg_lz_coverage_summary',
    count_column='lines_covered',
    sum_columns=['lines_total', 'lines_missed']
) }}
