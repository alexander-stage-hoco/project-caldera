{{ calculate_distribution_stats(
    tool_name='pmd-cpd',
    scope='direct',
    metrics_table='lz_pmd_cpd_file_metrics',
    metrics=['duplicate_lines', 'duplicate_blocks', 'duplication_percentage']
) }}
