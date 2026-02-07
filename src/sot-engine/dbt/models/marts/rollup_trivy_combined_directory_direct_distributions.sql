{{ calculate_distribution_stats(
    tool_name='trivy',
    scope='direct',
    metrics_table='stg_trivy_file_metrics',
    metrics=['vulnerability_count', 'iac_misconfig_count', 'total_finding_count', 'severity_high_plus'],
    use_ref=true
) }}
