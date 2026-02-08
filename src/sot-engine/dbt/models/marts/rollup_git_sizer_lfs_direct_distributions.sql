-- Git-sizer LFS candidate file size distributions per directory (direct scope)
-- Provides distribution statistics on the size of files recommended for LFS migration

{{ calculate_distribution_stats(
    tool_name='git-sizer',
    scope='direct',
    metrics_table='stg_git_sizer_lfs_file_metrics',
    metrics=['file_size_bytes'],
    use_ref=true
) }}
