-- Coverage distribution statistics per directory (recursive scope)
-- Aggregates line/branch coverage metrics for all files in directory subtree

{{ calculate_distribution_stats(
    tool_name='coverage-ingest',
    scope='recursive',
    metrics_table='lz_coverage_summary',
    metrics=['line_coverage_pct', 'branch_coverage_pct', 'lines_covered', 'lines_total']
) }}
