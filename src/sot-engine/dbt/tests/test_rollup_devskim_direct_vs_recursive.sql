-- Verifies that recursive rollup counts are always >= direct rollup counts
-- for the same directory (since recursive includes all descendants).
select
    r.run_pk,
    r.directory_id,
    r.file_count as recursive_file_count,
    d.file_count as direct_file_count,
    r.files_with_issues as recursive_files_with_issues,
    d.files_with_issues as direct_files_with_issues,
    r.total_issue_count as recursive_issue_count,
    d.total_issue_count as direct_issue_count
from {{ ref('rollup_devskim_directory_counts_recursive') }} r
join {{ ref('rollup_devskim_directory_counts_direct') }} d
    on d.run_pk = r.run_pk
    and d.directory_id = r.directory_id
where r.file_count < d.file_count
   or r.files_with_issues < d.files_with_issues
   or r.total_issue_count < d.total_issue_count
   or r.severity_critical < d.severity_critical
   or r.severity_high < d.severity_high
   or r.severity_medium < d.severity_medium
   or r.severity_low < d.severity_low
