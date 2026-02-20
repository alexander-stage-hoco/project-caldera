-- Validates that recursive counts >= direct counts for each directory
-- This invariant must hold: a directory's recursive count includes all
-- files in its subtree, while direct only counts files directly in that directory.

select
    r.run_pk,
    r.directory_id,
    r.file_count as recursive_file_count,
    d.file_count as direct_file_count,
    r.total_finding_count as recursive_finding_count,
    d.total_finding_count as direct_finding_count
from {{ ref('rollup_trivy_combined_directory_counts_recursive') }} r
join {{ ref('rollup_trivy_combined_directory_counts_direct') }} d
    on d.run_pk = r.run_pk
    and d.directory_id = r.directory_id
where r.file_count < d.file_count
   or r.files_with_vulns < d.files_with_vulns
   or r.files_with_iac_misconfigs < d.files_with_iac_misconfigs
   or r.total_vulnerability_count < d.total_vulnerability_count
   or r.total_vuln_critical < d.total_vuln_critical
   or r.total_vuln_high < d.total_vuln_high
   or r.total_vuln_medium < d.total_vuln_medium
   or r.total_vuln_low < d.total_vuln_low
   or r.total_iac_misconfig_count < d.total_iac_misconfig_count
   or r.total_iac_critical < d.total_iac_critical
   or r.total_iac_high < d.total_iac_high
   or r.total_iac_medium < d.total_iac_medium
   or r.total_iac_low < d.total_iac_low
   or r.total_finding_count < d.total_finding_count
   or r.total_severity_high_plus < d.total_severity_high_plus
