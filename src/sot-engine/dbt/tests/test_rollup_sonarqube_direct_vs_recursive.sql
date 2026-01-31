-- Validates that recursive counts >= direct counts for each directory
-- This invariant must hold: a directory's recursive count includes all
-- files in its subtree, while direct only counts files directly in that directory.

select
    r.run_pk,
    r.directory_id,
    r.total_issue_count as recursive_issue_count,
    d.total_issue_count as direct_issue_count,
    r.file_count as recursive_file_count,
    d.file_count as direct_file_count,
    r.files_with_issues as recursive_files_with_issues,
    d.files_with_issues as direct_files_with_issues
from {{ ref('rollup_sonarqube_directory_counts_recursive') }} r
join {{ ref('rollup_sonarqube_directory_counts_direct') }} d
    on d.run_pk = r.run_pk
    and d.directory_id = r.directory_id
where r.total_issue_count < d.total_issue_count
   or r.file_count < d.file_count
   or r.files_with_issues < d.files_with_issues
   or r.type_bug < d.type_bug
   or r.type_vulnerability < d.type_vulnerability
   or r.type_code_smell < d.type_code_smell
   or r.type_security_hotspot < d.type_security_hotspot
   or r.severity_blocker < d.severity_blocker
   or r.severity_critical < d.severity_critical
   or r.severity_major < d.severity_major
   or r.severity_minor < d.severity_minor
   or r.severity_info < d.severity_info
   or r.total_ncloc < d.total_ncloc
   or r.total_complexity < d.total_complexity
   or r.total_cognitive_complexity < d.total_cognitive_complexity
   or r.total_duplicated_lines < d.total_duplicated_lines
