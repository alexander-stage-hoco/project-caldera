{% snapshot snap_unified_repo_metrics %}

{{
    config(
        target_schema='snapshots',
        unique_key='collection_run_id',
        strategy='check',
        check_cols=[
            'health_grade', 'commit_count', 'blob_total_size',
            'violation_count', 'lfs_candidate_count',
            'author_count', 'total_loc', 'hhi_index', 'bus_factor',
            'top_author_pct'
        ]
    )
}}

select * from {{ ref('unified_repo_metrics') }}

{% endsnapshot %}
