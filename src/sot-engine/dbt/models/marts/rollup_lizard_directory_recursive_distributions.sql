{{ calculate_distribution_stats(
    tool_name='lizard',
    scope='recursive',
    metrics_table='lz_lizard_file_metrics',
    metrics=['nloc', 'total_ccn', 'avg_ccn', 'max_ccn']
) }}
