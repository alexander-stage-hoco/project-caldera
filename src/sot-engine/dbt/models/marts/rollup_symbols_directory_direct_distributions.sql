{{ calculate_distribution_stats(
    tool_name='symbol-scanner',
    scope='direct',
    metrics_table='stg_symbols_file_metrics',
    metrics=['symbol_count', 'function_count', 'class_count', 'exported_count', 'avg_parameters'],
    use_ref=true
) }}
