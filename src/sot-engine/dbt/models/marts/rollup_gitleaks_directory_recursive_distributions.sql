{{ calculate_distribution_stats(
    tool_name='gitleaks',
    scope='recursive',
    metrics_table='stg_gitleaks_secrets',
    metrics=['secret_count', 'severity_high_plus'],
    use_ref=true
) }}
