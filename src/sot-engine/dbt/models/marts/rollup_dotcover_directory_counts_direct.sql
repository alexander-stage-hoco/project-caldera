-- Dotcover coverage counts per directory (direct - only files in that directory)

{{ calculate_count_stats(
    tool_name='dotcover',
    scope='direct',
    staging_model='stg_dotcover_file_metrics',
    count_column='type_count',
    sum_columns=['covered_statements', 'total_statements']
) }}
