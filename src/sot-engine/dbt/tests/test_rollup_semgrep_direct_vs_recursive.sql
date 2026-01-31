-- Validates that recursive counts >= direct counts for each directory
-- This invariant must hold: a directory's recursive count includes all
-- files in its subtree, while direct only counts files directly in that directory.

select
    r.run_pk,
    r.directory_id,
    r.total_smell_count as recursive_smell_count,
    d.total_smell_count as direct_smell_count,
    r.file_count as recursive_file_count,
    d.file_count as direct_file_count,
    r.files_with_smells as recursive_files_with_smells,
    d.files_with_smells as direct_files_with_smells
from {{ ref('rollup_semgrep_directory_counts_recursive') }} r
join {{ ref('rollup_semgrep_directory_counts_direct') }} d
    on d.run_pk = r.run_pk
    and d.directory_id = r.directory_id
where r.total_smell_count < d.total_smell_count
   or r.file_count < d.file_count
   or r.files_with_smells < d.files_with_smells
   or r.severity_critical < d.severity_critical
   or r.severity_high < d.severity_high
   or r.severity_medium < d.severity_medium
   or r.severity_low < d.severity_low
   or r.severity_info < d.severity_info
