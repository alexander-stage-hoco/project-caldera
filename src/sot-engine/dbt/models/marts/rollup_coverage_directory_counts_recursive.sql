-- Coverage-ingest line counts per directory (recursive - includes subtree)

{{ calculate_count_stats(
    tool_name='coverage-ingest',
    scope='recursive',
    staging_model='stg_lz_coverage_summary',
    count_column='lines_covered',
    sum_columns=['lines_total', 'lines_missed']
) }}
