-- Validates that recursive counts >= direct counts for each directory
-- This invariant must hold: a directory's recursive count includes all
-- files in its subtree, while direct only counts files directly in that directory.

select
    r.run_pk,
    r.directory_id,
    r.total_license_count as recursive_license_count,
    d.total_license_count as direct_license_count,
    r.file_count as recursive_file_count,
    d.file_count as direct_file_count
from {{ ref('rollup_scancode_directory_counts_recursive') }} r
join {{ ref('rollup_scancode_directory_counts_direct') }} d
    on d.run_pk = r.run_pk
    and d.directory_id = r.directory_id
where r.total_license_count < d.total_license_count
   or r.file_count < d.file_count
   or r.total_cat_copyleft < d.total_cat_copyleft
   or r.total_cat_permissive < d.total_cat_permissive
   or r.total_cat_weak_copyleft < d.total_cat_weak_copyleft
   or r.total_cat_unknown < d.total_cat_unknown
   or r.total_match_file < d.total_match_file
   or r.total_match_header < d.total_match_header
   or r.total_match_spdx < d.total_match_spdx
