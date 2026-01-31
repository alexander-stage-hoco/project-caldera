{{ calculate_distribution_stats(
    tool_name='scc',
    scope='recursive',
    metrics_table='lz_scc_file_metrics',
    metrics=['lines_total', 'code_lines', 'comment_lines', 'blank_lines', 'complexity']
) }}
