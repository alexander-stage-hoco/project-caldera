-- Validates that recursive counts >= direct counts for each directory
-- This invariant must hold: a directory's recursive count includes all
-- files in its subtree, while direct only counts files directly in that directory.
-- Note: avg_parameters is skipped (average-of-averages, not monotonic)

select
    r.run_pk,
    r.directory_id,
    r.symbol_count as recursive_symbol_count,
    d.symbol_count as direct_symbol_count,
    r.file_count as recursive_file_count,
    d.file_count as direct_file_count
from {{ ref('rollup_symbols_directory_counts_recursive') }} r
join {{ ref('rollup_symbols_directory_counts_direct') }} d
    on d.run_pk = r.run_pk
    and d.directory_id = r.directory_id
where r.symbol_count < d.symbol_count
   or r.file_count < d.file_count
   or r.function_count < d.function_count
   or r.class_count < d.class_count
   or r.method_count < d.method_count
   or r.exported_count < d.exported_count
