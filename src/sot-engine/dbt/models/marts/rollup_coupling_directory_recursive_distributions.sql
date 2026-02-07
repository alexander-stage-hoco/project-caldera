{{ calculate_distribution_stats(
    tool_name='symbol-scanner',
    scope='recursive',
    metrics_table='stg_coupling_file_metrics',
    metrics=['total_fan_out', 'total_fan_in', 'total_coupling', 'avg_instability'],
    use_ref=true
) }}
