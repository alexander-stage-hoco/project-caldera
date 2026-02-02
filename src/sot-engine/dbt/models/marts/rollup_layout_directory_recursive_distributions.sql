{{ calculate_distribution_stats(
    tool_name='layout',
    scope='recursive',
    metrics_table='lz_layout_files',
    metrics=['size_bytes', 'line_count']
) }}
