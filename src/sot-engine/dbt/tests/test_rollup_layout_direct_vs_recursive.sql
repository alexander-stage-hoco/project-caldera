-- Validates that recursive counts >= direct counts for each directory
-- This invariant must hold: a directory's recursive count includes all
-- files in its subtree, while direct only counts files directly in that directory.

select
    r.run_pk,
    r.directory_id,
    r.file_count as recursive_file_count,
    d.file_count as direct_file_count,
    r.total_size_bytes as recursive_size_bytes,
    d.total_size_bytes as direct_size_bytes,
    r.total_line_count as recursive_line_count,
    d.total_line_count as direct_line_count
from {{ ref('rollup_layout_directory_counts_recursive') }} r
join {{ ref('rollup_layout_directory_counts_direct') }} d
    on d.run_pk = r.run_pk
    and d.directory_id = r.directory_id
where r.file_count < d.file_count
   or r.total_size_bytes < d.total_size_bytes
   or r.total_line_count < d.total_line_count
