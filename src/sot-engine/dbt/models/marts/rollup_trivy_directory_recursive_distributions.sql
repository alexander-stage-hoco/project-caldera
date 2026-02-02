{{ calculate_distribution_stats(
    tool_name='trivy',
    scope='recursive',
    metrics_table='stg_trivy_target_metrics',
    metrics=['vulnerability_count', 'severity_weighted_score'],
    use_ref=true
) }}
