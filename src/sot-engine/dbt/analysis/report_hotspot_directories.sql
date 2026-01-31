{% set run_pk = var('run_pk') %}
{% set limit_rows = var('limit', 10) %}

with scc as (
    select *
    from {{ ref('rollup_scc_directory_recursive_distributions') }}
    where run_pk = {{ run_pk }}
      and metric = 'lines_total'
),
lizard as (
    select *
    from {{ ref('rollup_lizard_directory_recursive_distributions') }}
    where run_pk = {{ run_pk }}
      and metric = 'total_ccn'
),
loc_ranked as (
    select
        'loc_hotspot' as category,
        directory_path,
        value_count,
        avg_value,
        p95_value,
        p99_value,
        gini_value,
        hoover_value,
        palma_value,
        top_20_pct_share,
        row_number() over (
            order by p95_value desc, avg_value desc, directory_path
        ) as rank_id
    from scc
),
ccn_ranked as (
    select
        'complexity_hotspot' as category,
        directory_path,
        value_count,
        avg_value,
        p95_value,
        p99_value,
        gini_value,
        hoover_value,
        palma_value,
        top_20_pct_share,
        row_number() over (
            order by p95_value desc, avg_value desc, directory_path
        ) as rank_id
    from lizard
)
select *
from loc_ranked
where rank_id <= {{ limit_rows }}
union all
select *
from ccn_ranked
where rank_id <= {{ limit_rows }}
order by category, rank_id
