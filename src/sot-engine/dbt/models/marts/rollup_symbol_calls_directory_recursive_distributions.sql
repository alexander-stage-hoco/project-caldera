{{ calculate_distribution_stats(
    tool_name='symbol-scanner',
    scope='recursive',
    metrics_table='stg_symbol_calls_file_metrics',
    metrics=['call_count', 'distinct_callees', 'distinct_callee_files', 'direct_call_count'],
    use_ref=true
) }}
