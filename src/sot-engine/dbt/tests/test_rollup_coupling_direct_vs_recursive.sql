-- Validate recursive >= direct invariants for coupling metrics
-- For any given directory, recursive counts must be >= direct counts
-- because recursive includes all files in the subtree while direct
-- includes only files directly in that directory.
select
    r.run_pk,
    r.directory_id,
    r.fan_in as recursive_fan_in,
    d.fan_in as direct_fan_in,
    r.fan_out as recursive_fan_out,
    d.fan_out as direct_fan_out,
    r.outgoing_calls as recursive_outgoing_calls,
    d.outgoing_calls as direct_outgoing_calls
from {{ ref('rollup_coupling_directory_metrics_recursive') }} r
join {{ ref('rollup_coupling_directory_metrics_direct') }} d
    on d.run_pk = r.run_pk
    and d.directory_id = r.directory_id
where r.fan_in < d.fan_in
   or r.fan_out < d.fan_out
   or r.outgoing_calls < d.outgoing_calls
