-- Roslyn violation counts per directory (direct - only files in that directory)

{{ calculate_count_stats(
    tool_name='roslyn-analyzers',
    scope='direct',
    staging_model='stg_roslyn_file_metrics',
    count_column='violation_count',
    sum_columns=['severity_high_plus', 'cat_security', 'cat_design', 'cat_resource', 'cat_dead_code', 'cat_performance']
) }}
