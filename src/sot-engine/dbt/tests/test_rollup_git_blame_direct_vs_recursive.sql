-- Validates that recursive counts >= direct counts for each directory
-- This invariant must hold: a directory's recursive count includes all
-- files in its subtree, while direct only counts files directly in that directory.

select
    r.run_pk,
    r.directory_id,
    r.file_count as recursive_file_count,
    d.file_count as direct_file_count,
    r.total_lines as recursive_total_lines,
    d.total_lines as direct_total_lines,
    r.knowledge_silo_count as recursive_silos,
    d.knowledge_silo_count as direct_silos
from {{ ref('rollup_git_blame_directory_counts_recursive') }} r
join {{ ref('rollup_git_blame_directory_counts_direct') }} d
    on d.run_pk = r.run_pk
    and d.directory_id = r.directory_id
where r.file_count < d.file_count
   or r.total_lines < d.total_lines
   or r.knowledge_silo_count < d.knowledge_silo_count
   or r.single_author_files < d.single_author_files
   or r.high_concentration_files < d.high_concentration_files
   or r.stale_file_count < d.stale_file_count
