-- Coverage distribution statistics per directory (direct scope)
-- Aggregates line/branch coverage metrics for files directly in each directory

{{ calculate_distribution_stats(
    tool_name='coverage-ingest',
    scope='direct',
    metrics_table='lz_coverage_summary',
    metrics=['line_coverage_pct', 'branch_coverage_pct', 'lines_covered', 'lines_total']
) }}
