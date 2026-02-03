{{ calculate_distribution_stats(
    tool_name='symbol-scanner',
    scope='recursive',
    metrics_table='stg_file_imports_file_metrics',
    metrics=['import_count', 'unique_imports', 'static_import_count'],
    use_ref=true
) }}
