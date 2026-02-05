-- Scancode license counts per directory (recursive - includes subtree)

{{ calculate_count_stats(
    tool_name='scancode',
    scope='recursive',
    staging_model='stg_scancode_file_metrics',
    count_column='license_count',
    sum_columns=['cat_copyleft', 'cat_permissive', 'cat_weak_copyleft', 'cat_unknown', 'match_file', 'match_header', 'match_spdx']
) }}
