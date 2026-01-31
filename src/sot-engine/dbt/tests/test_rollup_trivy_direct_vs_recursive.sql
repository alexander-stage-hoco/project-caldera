-- Validates that recursive counts >= direct counts for each directory
-- This invariant must hold: a directory's recursive count includes all
-- files in its subtree, while direct only counts files directly in that directory.

select
    r.run_pk,
    r.directory_id,
    r.target_count as recursive_target_count,
    d.target_count as direct_target_count,
    r.files_with_vulns as recursive_files_with_vulns,
    d.files_with_vulns as direct_files_with_vulns,
    r.total_vulnerability_count as recursive_vuln_count,
    d.total_vulnerability_count as direct_vuln_count,
    r.total_iac_misconfig_count as recursive_iac_count,
    d.total_iac_misconfig_count as direct_iac_count
from {{ ref('rollup_trivy_directory_counts_recursive') }} r
join {{ ref('rollup_trivy_directory_counts_direct') }} d
    on d.run_pk = r.run_pk
    and d.directory_id = r.directory_id
where r.target_count < d.target_count
   or r.files_with_vulns < d.files_with_vulns
   or r.total_vulnerability_count < d.total_vulnerability_count
   or r.vuln_critical_count < d.vuln_critical_count
   or r.vuln_high_count < d.vuln_high_count
   or r.vuln_medium_count < d.vuln_medium_count
   or r.vuln_low_count < d.vuln_low_count
   or r.files_with_iac_misconfigs < d.files_with_iac_misconfigs
   or r.total_iac_misconfig_count < d.total_iac_misconfig_count
   or r.iac_critical_count < d.iac_critical_count
   or r.iac_high_count < d.iac_high_count
   or r.iac_medium_count < d.iac_medium_count
   or r.iac_low_count < d.iac_low_count
