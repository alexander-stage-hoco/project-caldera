{% snapshot snap_unified_run_summary %}

{{
    config(
        target_schema='snapshots',
        unique_key='run_pk',
        strategy='check',
        check_cols=[
            'total_files', 'total_loc', 'total_code', 'total_comment',
            'total_blank', 'total_ccn', 'avg_ccn', 'max_ccn',
            'overall_coverage_pct', 'scc_file_count', 'lizard_file_count',
            'dotcover_file_count',
            'trust_score', 'warning_count', 'budget_passed'
        ]
    )
}}

select * from {{ ref('unified_run_summary') }}

{% endsnapshot %}
