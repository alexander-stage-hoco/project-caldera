{{ calculate_distribution_stats(
    tool_name='layout',
    scope='direct',
    metrics_table='lz_layout_files',
    metrics=['size_bytes', 'line_count']
) }}
