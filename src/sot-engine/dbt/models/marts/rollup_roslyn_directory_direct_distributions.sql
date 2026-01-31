{{ calculate_distribution_stats(
    tool_name='roslyn',
    scope='direct',
    metrics_table='stg_roslyn_file_metrics',
    metrics=[
        'violation_count',
        'severity_high_plus',
        'severity_critical',
        'severity_high',
        'severity_medium',
        'severity_low',
        'severity_info',
        'cat_security',
        'cat_design',
        'cat_resource',
        'cat_dead_code',
        'cat_performance',
        'cat_other'
    ],
    use_ref=true
) }}
