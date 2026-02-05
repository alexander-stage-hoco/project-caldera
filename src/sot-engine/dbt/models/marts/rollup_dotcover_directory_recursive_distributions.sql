{{ calculate_distribution_stats(
    tool_name='dotcover',
    scope='recursive',
    metrics_table='stg_dotcover_file_metrics',
    metrics=['statement_coverage_pct', 'type_count'],
    use_ref=true
) }}
