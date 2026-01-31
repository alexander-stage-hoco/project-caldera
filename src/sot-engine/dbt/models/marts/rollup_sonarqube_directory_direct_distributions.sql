{{ calculate_distribution_stats(
    tool_name='sonarqube',
    scope='direct',
    metrics_table='stg_sonarqube_file_metrics',
    metrics=['issue_count', 'severity_high_plus', 'ncloc', 'complexity', 'cognitive_complexity'],
    use_ref=true
) }}
