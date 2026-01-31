select
    r.run_pk,
    r.directory_id,
    r.metric,
    r.value_count as recursive_value_count,
    d.value_count as direct_value_count,
    r.min_value as recursive_min,
    r.max_value as recursive_max,
    d.min_value as direct_min,
    d.max_value as direct_max
from {{ ref('rollup_lizard_directory_recursive_distributions') }} r
join {{ ref('rollup_lizard_directory_direct_distributions') }} d
    on d.run_pk = r.run_pk
    and d.directory_id = r.directory_id
    and d.metric = r.metric
where r.value_count < d.value_count
   or r.min_value > d.min_value
   or r.max_value < d.max_value
