-- Unified directory metrics combining all tool rollups (recursive scope)
-- Complements unified_file_metrics with directory-level cross-tool analysis
-- Uses layout-scanner directories as the spine, joining all tool rollups

with tool_runs as (
    select run_pk, collection_run_id, tool_name
    from {{ source('lz', 'lz_tool_runs') }}
),

-- Layout as spine: every directory in the collection
layout_dirs as (
    select
        tr.collection_run_id,
        ld.run_pk as layout_run_pk,
        ld.directory_id,
        ld.directory_path,
        ld.file_count as layout_file_count,
        ld.binary_file_count,
        ld.total_size_bytes,
        ld.total_line_count,
        ld.language_count,
        ld.category_count
    from {{ ref('rollup_layout_directory_counts_recursive') }} ld
    join tool_runs tr
        on tr.run_pk = ld.run_pk
        and tr.tool_name in ('layout', 'layout-scanner')
),

-- SCC: lines of code and complexity
scc_dirs as (
    select tr.collection_run_id, s.*
    from {{ ref('rollup_scc_directory_counts_recursive') }} s
    join tool_runs tr on tr.run_pk = s.run_pk and tr.tool_name = 'scc'
),

-- Lizard: cyclomatic complexity
lizard_dirs as (
    select tr.collection_run_id, l.*
    from {{ ref('rollup_lizard_directory_counts_recursive') }} l
    join tool_runs tr on tr.run_pk = l.run_pk and tr.tool_name = 'lizard'
),

-- Symbol scanner: symbol counts
symbol_dirs as (
    select tr.collection_run_id, s.*
    from {{ ref('rollup_symbols_directory_counts_recursive') }} s
    join tool_runs tr on tr.run_pk = s.run_pk and tr.tool_name = 'symbol-scanner'
),

-- Symbol calls: function call counts
call_dirs as (
    select tr.collection_run_id, c.*
    from {{ ref('rollup_symbol_calls_directory_counts_recursive') }} c
    join tool_runs tr on tr.run_pk = c.run_pk and tr.tool_name = 'symbol-scanner'
),

-- Coupling: fan-in/fan-out
coupling_dirs as (
    select tr.collection_run_id, cp.*
    from {{ ref('rollup_coupling_directory_metrics_recursive') }} cp
    join tool_runs tr on tr.run_pk = cp.run_pk and tr.tool_name = 'symbol-scanner'
),

-- File imports
import_dirs as (
    select tr.collection_run_id, i.*
    from {{ ref('rollup_file_imports_directory_counts_recursive') }} i
    join tool_runs tr on tr.run_pk = i.run_pk and tr.tool_name = 'symbol-scanner'
),

-- Coverage ingest: line/branch coverage
coverage_dirs as (
    select tr.collection_run_id, c.*
    from {{ ref('rollup_coverage_directory_counts_recursive') }} c
    join tool_runs tr on tr.run_pk = c.run_pk and tr.tool_name = 'coverage-ingest'
),

-- Dotcover: .NET statement coverage
dotcover_dirs as (
    select tr.collection_run_id, d.*
    from {{ ref('rollup_dotcover_directory_counts_recursive') }} d
    join tool_runs tr on tr.run_pk = d.run_pk and tr.tool_name = 'dotcover'
),

-- Roslyn: .NET analyzer violations
roslyn_dirs as (
    select tr.collection_run_id, r.*
    from {{ ref('rollup_roslyn_directory_counts_recursive') }} r
    join tool_runs tr on tr.run_pk = r.run_pk and tr.tool_name = 'roslyn-analyzers'
),

-- Semgrep: code smells
semgrep_dirs as (
    select tr.collection_run_id, s.*
    from {{ ref('rollup_semgrep_directory_counts_recursive') }} s
    join tool_runs tr on tr.run_pk = s.run_pk and tr.tool_name = 'semgrep'
),

-- DevSkim: security linting
devskim_dirs as (
    select tr.collection_run_id, d.*
    from {{ ref('rollup_devskim_directory_counts_recursive') }} d
    join tool_runs tr on tr.run_pk = d.run_pk and tr.tool_name = 'devskim'
),

-- SonarQube: issues and cognitive complexity
sonarqube_dirs as (
    select tr.collection_run_id, s.*
    from {{ ref('rollup_sonarqube_directory_counts_recursive') }} s
    join tool_runs tr on tr.run_pk = s.run_pk and tr.tool_name = 'sonarqube'
),

-- Gitleaks: secret detection
gitleaks_dirs as (
    select tr.collection_run_id, g.*
    from {{ ref('rollup_gitleaks_directory_counts_recursive') }} g
    join tool_runs tr on tr.run_pk = g.run_pk and tr.tool_name = 'gitleaks'
),

-- Trivy: vulnerabilities and IaC misconfigs (combined model uses layout_run_pk)
trivy_dirs as (
    select
        tr.collection_run_id,
        t.run_pk as layout_run_pk,
        t.tool_run_pk,
        t.directory_id,
        t.directory_path,
        t.file_count,
        t.files_with_vulns,
        t.files_with_iac_misconfigs,
        t.total_vulnerability_count,
        t.total_vuln_critical,
        t.total_vuln_high,
        t.total_vuln_medium,
        t.total_vuln_low,
        t.total_iac_misconfig_count,
        t.total_iac_critical,
        t.total_iac_high,
        t.total_iac_medium,
        t.total_iac_low,
        t.total_finding_count,
        t.total_severity_high_plus
    from {{ ref('rollup_trivy_combined_directory_counts_recursive') }} t
    join tool_runs tr
        on tr.run_pk = t.run_pk
        and tr.tool_name in ('layout', 'layout-scanner')
),

-- Scancode: license detection
scancode_dirs as (
    select tr.collection_run_id, s.*
    from {{ ref('rollup_scancode_directory_counts_recursive') }} s
    join tool_runs tr on tr.run_pk = s.run_pk and tr.tool_name = 'scancode'
),

-- PMD-CPD: copy-paste detection
pmd_cpd_dirs as (
    select tr.collection_run_id, p.*
    from {{ ref('rollup_pmd_cpd_directory_counts_recursive') }} p
    join tool_runs tr on tr.run_pk = p.run_pk and tr.tool_name = 'pmd-cpd'
),

-- Git blame: authorship and knowledge risk
blame_dirs as (
    select tr.collection_run_id, b.*
    from {{ ref('rollup_git_blame_directory_counts_recursive') }} b
    join tool_runs tr on tr.run_pk = b.run_pk and tr.tool_name = 'git-blame-scanner'
)

select
    lay.layout_run_pk as run_pk,
    lay.collection_run_id,
    lay.directory_id,
    lay.directory_path,

    -- Layout: file structure
    lay.layout_file_count as file_count,
    lay.binary_file_count,
    lay.total_size_bytes,
    lay.total_line_count,
    lay.language_count,
    lay.category_count,

    -- SCC: lines of code
    scc.total_lines as loc_total,
    scc.total_code_lines as loc_code,
    scc.total_comment_lines as loc_comment,
    scc.total_blank_lines as loc_blank,
    scc.total_complexity as scc_complexity,
    scc.minified_count,
    scc.generated_count,

    -- Lizard: cyclomatic complexity
    liz.total_nloc as lizard_nloc,
    liz.total_function_count as lizard_function_count,
    liz.total_ccn as lizard_total_ccn,
    liz.avg_ccn as lizard_avg_ccn,
    liz.max_ccn as lizard_max_ccn,

    -- Symbol scanner: code symbols
    sym.symbol_count,
    sym.function_count as symbol_function_count,
    sym.class_count as symbol_class_count,
    sym.method_count as symbol_method_count,
    sym.exported_count as symbol_exported_count,
    sym.avg_parameters as symbol_avg_parameters,

    -- Symbol calls: function calls
    cal.total_call_count,
    cal.total_distinct_callees,
    cal.total_distinct_callee_files,
    cal.total_direct_call_count,
    cal.total_dynamic_call_count,
    cal.total_async_call_count,

    -- Coupling: fan-in/fan-out
    cpl.fan_out as coupling_fan_out,
    cpl.fan_in as coupling_fan_in,
    cpl.outgoing_calls as coupling_outgoing_calls,
    cpl.instability as coupling_instability,

    -- Imports
    imp.total_import_count,
    imp.total_unique_imports,

    -- Coverage ingest: line/branch coverage
    cov.total_lines_covered as coverage_lines_covered,
    cov.total_lines_total as coverage_lines_total,
    cov.total_lines_missed as coverage_lines_missed,
    case
        when cov.total_lines_total > 0
        then round(100.0 * cov.total_lines_covered / cov.total_lines_total, 2)
        else null
    end as coverage_line_pct,

    -- Dotcover: .NET coverage
    dc.total_type_count as dotcover_type_count,
    dc.total_covered_statements as dotcover_covered_statements,
    dc.total_total_statements as dotcover_total_statements,
    case
        when dc.total_total_statements > 0
        then round(100.0 * dc.total_covered_statements / dc.total_total_statements, 2)
        else null
    end as dotcover_coverage_pct,

    -- Roslyn: .NET violations
    ros.total_violation_count as roslyn_violation_count,
    ros.total_severity_high_plus as roslyn_severity_high_plus,
    ros.total_cat_security as roslyn_cat_security,
    ros.total_cat_design as roslyn_cat_design,

    -- Semgrep: code smells (hand-crafted rollup: no total_ prefix on severity)
    sem.total_smell_count as semgrep_smell_count,
    sem.severity_high_plus as semgrep_severity_high_plus,

    -- DevSkim: security issues (hand-crafted rollup)
    dsk.total_issue_count as devskim_issue_count,
    dsk.severity_high_plus as devskim_severity_high_plus,

    -- SonarQube: issues (hand-crafted rollup)
    sq.total_issue_count as sonarqube_issue_count,
    sq.type_bug as sonarqube_type_bug,
    sq.type_vulnerability as sonarqube_type_vulnerability,
    sq.type_code_smell as sonarqube_type_code_smell,
    sq.severity_high_plus as sonarqube_severity_high_plus,
    sq.total_cognitive_complexity as sonarqube_cognitive_complexity,
    sq.total_duplicated_lines as sonarqube_duplicated_lines,

    -- Gitleaks: secrets (hand-crafted rollup)
    gl.total_secret_count as gitleaks_secret_count,
    gl.severity_high_plus as gitleaks_severity_high_plus,
    gl.secrets_in_head as gitleaks_secrets_in_head,
    gl.secrets_in_history as gitleaks_secrets_in_history,

    -- Trivy: vulnerabilities and IaC
    tv.total_vulnerability_count as trivy_vulnerability_count,
    tv.total_vuln_critical as trivy_vuln_critical,
    tv.total_vuln_high as trivy_vuln_high,
    tv.total_iac_misconfig_count as trivy_iac_misconfig_count,
    tv.total_finding_count as trivy_total_finding_count,
    tv.total_severity_high_plus as trivy_severity_high_plus,

    -- Scancode: licenses
    sc.total_license_count as scancode_license_count,
    sc.total_cat_copyleft as scancode_cat_copyleft,
    sc.total_cat_permissive as scancode_cat_permissive,

    -- PMD-CPD: duplication
    pmd.total_duplicate_lines as pmd_cpd_duplicate_lines,
    pmd.total_duplicate_blocks as pmd_cpd_duplicate_blocks,
    pmd.avg_duplication_percentage as pmd_cpd_avg_duplication_pct,

    -- Git blame: authorship risk
    bl.avg_unique_authors as blame_avg_unique_authors,
    bl.max_unique_authors as blame_max_unique_authors,
    bl.avg_top_author_pct as blame_avg_top_author_pct,
    bl.single_author_files as blame_single_author_files,
    bl.high_concentration_files as blame_high_concentration_files,
    bl.knowledge_silo_count as blame_knowledge_silo_count,
    bl.stale_file_count as blame_stale_file_count,
    bl.total_churn_30d as blame_churn_30d,
    bl.total_churn_90d as blame_churn_90d,

    -- Sources tracking
    concat_ws(
        ',',
        'layout-scanner',
        case when scc.run_pk is not null then 'scc' end,
        case when liz.run_pk is not null then 'lizard' end,
        case when sym.run_pk is not null then 'symbol-scanner' end,
        case when cov.run_pk is not null then 'coverage-ingest' end,
        case when dc.run_pk is not null then 'dotcover' end,
        case when ros.run_pk is not null then 'roslyn-analyzers' end,
        case when sem.run_pk is not null then 'semgrep' end,
        case when dsk.run_pk is not null then 'devskim' end,
        case when sq.run_pk is not null then 'sonarqube' end,
        case when gl.run_pk is not null then 'gitleaks' end,
        case when tv.tool_run_pk is not null then 'trivy' end,
        case when sc.run_pk is not null then 'scancode' end,
        case when pmd.run_pk is not null then 'pmd-cpd' end,
        case when bl.run_pk is not null then 'git-blame-scanner' end
    ) as sources

from layout_dirs lay

left join scc_dirs scc
    on scc.collection_run_id = lay.collection_run_id
    and scc.directory_id = lay.directory_id

left join lizard_dirs liz
    on liz.collection_run_id = lay.collection_run_id
    and liz.directory_id = lay.directory_id

left join symbol_dirs sym
    on sym.collection_run_id = lay.collection_run_id
    and sym.directory_id = lay.directory_id

left join call_dirs cal
    on cal.collection_run_id = lay.collection_run_id
    and cal.directory_id = lay.directory_id

left join coupling_dirs cpl
    on cpl.collection_run_id = lay.collection_run_id
    and cpl.directory_id = lay.directory_id

left join import_dirs imp
    on imp.collection_run_id = lay.collection_run_id
    and imp.directory_id = lay.directory_id

left join coverage_dirs cov
    on cov.collection_run_id = lay.collection_run_id
    and cov.directory_id = lay.directory_id

left join dotcover_dirs dc
    on dc.collection_run_id = lay.collection_run_id
    and dc.directory_id = lay.directory_id

left join roslyn_dirs ros
    on ros.collection_run_id = lay.collection_run_id
    and ros.directory_id = lay.directory_id

left join semgrep_dirs sem
    on sem.collection_run_id = lay.collection_run_id
    and sem.directory_id = lay.directory_id

left join devskim_dirs dsk
    on dsk.collection_run_id = lay.collection_run_id
    and dsk.directory_id = lay.directory_id

left join sonarqube_dirs sq
    on sq.collection_run_id = lay.collection_run_id
    and sq.directory_id = lay.directory_id

left join gitleaks_dirs gl
    on gl.collection_run_id = lay.collection_run_id
    and gl.directory_id = lay.directory_id

left join trivy_dirs tv
    on tv.collection_run_id = lay.collection_run_id
    and tv.directory_id = lay.directory_id

left join scancode_dirs sc
    on sc.collection_run_id = lay.collection_run_id
    and sc.directory_id = lay.directory_id

left join pmd_cpd_dirs pmd
    on pmd.collection_run_id = lay.collection_run_id
    and pmd.directory_id = lay.directory_id

left join blame_dirs bl
    on bl.collection_run_id = lay.collection_run_id
    and bl.directory_id = lay.directory_id
