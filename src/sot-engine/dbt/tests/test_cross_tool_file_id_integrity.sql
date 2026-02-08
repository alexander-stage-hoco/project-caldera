-- Test that all file_ids in tool staging models exist in layout_files
-- for the same collection_run. Returns orphaned file_ids (test passes if 0 rows).
with tool_file_refs as (
    select 'scc' as tool, s.run_pk, s.file_id, tr.collection_run_id
    from {{ ref('stg_lz_scc_file_metrics') }} s
    join {{ ref('stg_lz_tool_runs') }} tr on tr.run_pk = s.run_pk
    union all
    select 'lizard', l.run_pk, l.file_id, tr.collection_run_id
    from {{ ref('stg_lz_lizard_file_metrics') }} l
    join {{ ref('stg_lz_tool_runs') }} tr on tr.run_pk = l.run_pk
    union all
    select 'semgrep', sm.run_pk, sm.file_id, tr.collection_run_id
    from {{ ref('stg_lz_semgrep_smells') }} sm
    join {{ ref('stg_lz_tool_runs') }} tr on tr.run_pk = sm.run_pk
    union all
    select 'roslyn', r.run_pk, r.file_id, tr.collection_run_id
    from {{ ref('stg_lz_roslyn_violations') }} r
    join {{ ref('stg_lz_tool_runs') }} tr on tr.run_pk = r.run_pk
    union all
    select 'sonarqube', sq.run_pk, sq.file_id, tr.collection_run_id
    from {{ ref('stg_sonarqube_issues') }} sq
    join {{ ref('stg_lz_tool_runs') }} tr on tr.run_pk = sq.run_pk
    union all
    select 'trivy_targets', tt.run_pk, tt.file_id, tr.collection_run_id
    from {{ ref('stg_trivy_targets') }} tt
    join {{ ref('stg_lz_tool_runs') }} tr on tr.run_pk = tt.run_pk
    union all
    select 'trivy_iac', ti.run_pk, ti.file_id, tr.collection_run_id
    from {{ ref('stg_trivy_iac_misconfigs') }} ti
    join {{ ref('stg_lz_tool_runs') }} tr on tr.run_pk = ti.run_pk
    union all
    select 'gitleaks', gl.run_pk, gl.file_id, tr.collection_run_id
    from {{ ref('stg_lz_gitleaks_secrets') }} gl
    join {{ ref('stg_lz_tool_runs') }} tr on tr.run_pk = gl.run_pk
    union all
    select 'scancode', sc.run_pk, sc.file_id, tr.collection_run_id
    from {{ ref('stg_lz_scancode_file_licenses') }} sc
    join {{ ref('stg_lz_tool_runs') }} tr on tr.run_pk = sc.run_pk
    union all
    select 'pmd_cpd', p.run_pk, p.file_id, tr.collection_run_id
    from {{ ref('stg_lz_pmd_cpd_file_metrics') }} p
    join {{ ref('stg_lz_tool_runs') }} tr on tr.run_pk = p.run_pk
    union all
    select 'devskim', d.run_pk, d.file_id, tr.collection_run_id
    from {{ ref('stg_lz_devskim_findings') }} d
    join {{ ref('stg_lz_tool_runs') }} tr on tr.run_pk = d.run_pk
),
layout_runs as (
    select run_pk as layout_run_pk, collection_run_id
    from {{ ref('stg_lz_tool_runs') }}
    where tool_name in ('layout', 'layout-scanner')
),
orphaned_file_ids as (
    select tfr.tool, tfr.file_id, tfr.collection_run_id
    from tool_file_refs tfr
    join layout_runs lr on lr.collection_run_id = tfr.collection_run_id
    left join {{ ref('stg_lz_layout_files') }} lf
        on lf.run_pk = lr.layout_run_pk and lf.file_id = tfr.file_id
    where lf.file_id is null
)
select * from orphaned_file_ids
