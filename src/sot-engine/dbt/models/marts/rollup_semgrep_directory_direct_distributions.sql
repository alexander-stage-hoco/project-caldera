{{ calculate_distribution_stats(
    tool_name='semgrep',
    scope='direct',
    metrics_table='stg_semgrep_file_metrics',
    metrics=['smell_count', 'severity_high_plus'],
    use_ref=true
) }}
