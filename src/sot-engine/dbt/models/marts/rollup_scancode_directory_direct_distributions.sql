{{ calculate_distribution_stats(
    tool_name='scancode',
    scope='direct',
    metrics_table='stg_scancode_file_metrics',
    metrics=['license_count', 'avg_confidence'],
    use_ref=true
) }}
