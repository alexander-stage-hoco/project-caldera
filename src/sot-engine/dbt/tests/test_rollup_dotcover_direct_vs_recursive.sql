-- Validates that recursive counts >= direct counts for each directory
-- This invariant must hold: a directory's recursive count includes all
-- files in its subtree, while direct only counts files directly in that directory.

select
    r.run_pk,
    r.directory_id,
    r.total_type_count as recursive_type_count,
    d.total_type_count as direct_type_count,
    r.file_count as recursive_file_count,
    d.file_count as direct_file_count
from {{ ref('rollup_dotcover_directory_counts_recursive') }} r
join {{ ref('rollup_dotcover_directory_counts_direct') }} d
    on d.run_pk = r.run_pk
    and d.directory_id = r.directory_id
where r.total_type_count < d.total_type_count
   or r.file_count < d.file_count
   or r.total_covered_statements < d.total_covered_statements
   or r.total_total_statements < d.total_total_statements
