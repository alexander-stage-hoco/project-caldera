-- Scancode license counts per directory (direct - only files in that directory)

{{ calculate_count_stats(
    tool_name='scancode',
    scope='direct',
    staging_model='stg_scancode_file_metrics',
    count_column='license_count',
    sum_columns=['cat_copyleft', 'cat_permissive', 'cat_weak_copyleft', 'cat_unknown', 'match_file', 'match_header', 'match_spdx']
) }}
