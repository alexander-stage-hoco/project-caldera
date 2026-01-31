-- Validates that recursive counts >= direct counts for each directory
-- This invariant must hold: a directory's recursive count includes all
-- files in its subtree, while direct only counts files directly in that directory.

select
    r.run_pk,
    r.directory_id,
    r.total_violation_count as recursive_violation_count,
    d.total_violation_count as direct_violation_count,
    r.file_count as recursive_file_count,
    d.file_count as direct_file_count
from {{ ref('rollup_roslyn_directory_counts_recursive') }} r
join {{ ref('rollup_roslyn_directory_counts_direct') }} d
    on d.run_pk = r.run_pk
    and d.directory_id = r.directory_id
where r.total_violation_count < d.total_violation_count
   or r.file_count < d.file_count
   or r.total_severity_high_plus < d.total_severity_high_plus
   or r.total_cat_security < d.total_cat_security
   or r.total_cat_design < d.total_cat_design
   or r.total_cat_resource < d.total_cat_resource
   or r.total_cat_dead_code < d.total_cat_dead_code
   or r.total_cat_performance < d.total_cat_performance
