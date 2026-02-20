-- Validates that recursive counts >= direct counts for each directory
-- This invariant must hold: a directory's recursive count includes all
-- files in its subtree, while direct only counts files directly in that directory.

select
    r.run_pk,
    r.directory_id,
    r.file_count as recursive_file_count,
    d.file_count as direct_file_count,
    r.total_import_count as recursive_import_count,
    d.total_import_count as direct_import_count
from {{ ref('rollup_file_imports_directory_counts_recursive') }} r
join {{ ref('rollup_file_imports_directory_counts_direct') }} d
    on d.run_pk = r.run_pk
    and d.directory_id = r.directory_id
where r.file_count < d.file_count
   or r.total_import_count < d.total_import_count
   or r.total_unique_imports < d.total_unique_imports
   or r.total_static_import_count < d.total_static_import_count
   or r.total_dynamic_import_count < d.total_dynamic_import_count
   or r.total_side_effect_import_count < d.total_side_effect_import_count
