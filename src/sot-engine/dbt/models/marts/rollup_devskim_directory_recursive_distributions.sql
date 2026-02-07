{{ calculate_distribution_stats(
    tool_name='devskim',
    scope='recursive',
    metrics_table='stg_devskim_file_metrics',
    metrics=['issue_count', 'severity_high_plus'],
    use_ref=true
) }}
