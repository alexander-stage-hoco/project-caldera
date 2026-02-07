with scc_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'scc'
),
lizard_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'lizard'
),
dotcover_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'dotcover'
),
roslyn_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'roslyn-analyzers'
),
semgrep_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'semgrep'
),
devskim_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'devskim'
),
sonarqube_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'sonarqube'
),
symbol_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'symbol-scanner'
),
gitleaks_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'gitleaks'
),
trivy_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'trivy'
),
layout_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name in ('layout', 'layout-scanner')
),
scc_map as (
    select
        sr.run_pk as tool_run_pk,
        sr.collection_run_id,
        lr.run_pk as layout_run_pk,
        sg.run_pk as semgrep_run_pk,
        sym.run_pk as symbol_run_pk
    from scc_runs sr
    join layout_runs lr
        on lr.collection_run_id = sr.collection_run_id
    left join semgrep_runs sg
        on sg.collection_run_id = sr.collection_run_id
    left join symbol_runs sym
        on sym.collection_run_id = sr.collection_run_id
),
lizard_map as (
    select
        lr.run_pk as tool_run_pk,
        lr.collection_run_id,
        lrn.run_pk as layout_run_pk,
        sg.run_pk as semgrep_run_pk,
        sym.run_pk as symbol_run_pk
    from lizard_runs lr
    join layout_runs lrn
        on lrn.collection_run_id = lr.collection_run_id
    left join semgrep_runs sg
        on sg.collection_run_id = lr.collection_run_id
    left join symbol_runs sym
        on sym.collection_run_id = lr.collection_run_id
),
dotcover_map as (
    select
        dr.run_pk as tool_run_pk,
        dr.collection_run_id,
        lr.run_pk as layout_run_pk
    from dotcover_runs dr
    join layout_runs lr on lr.collection_run_id = dr.collection_run_id
),
roslyn_map as (
    select
        rr.run_pk as tool_run_pk,
        rr.collection_run_id,
        lr.run_pk as layout_run_pk
    from roslyn_runs rr
    join layout_runs lr on lr.collection_run_id = rr.collection_run_id
),
devskim_map as (
    select
        dr.run_pk as tool_run_pk,
        dr.collection_run_id,
        lr.run_pk as layout_run_pk
    from devskim_runs dr
    join layout_runs lr on lr.collection_run_id = dr.collection_run_id
),
sonarqube_map as (
    select
        sr.run_pk as tool_run_pk,
        sr.collection_run_id,
        lr.run_pk as layout_run_pk
    from sonarqube_runs sr
    join layout_runs lr on lr.collection_run_id = sr.collection_run_id
),
gitleaks_map as (
    select
        gr.run_pk as tool_run_pk,
        gr.collection_run_id,
        lr.run_pk as layout_run_pk
    from gitleaks_runs gr
    join layout_runs lr
        on lr.collection_run_id = gr.collection_run_id
),
trivy_map as (
    select
        tr.run_pk as tool_run_pk,
        tr.collection_run_id,
        lr.run_pk as layout_run_pk
    from trivy_runs tr
    join layout_runs lr
        on lr.collection_run_id = tr.collection_run_id
),
scc_files as (
    select
        sm.run_pk,
        rm.collection_run_id,
        rm.layout_run_pk,
        rm.semgrep_run_pk,
        rm.symbol_run_pk,
        sm.file_id,
        sm.lines_total,
        sm.code_lines,
        sm.comment_lines,
        sm.blank_lines,
        sm.complexity
    from {{ source('lz', 'lz_scc_file_metrics') }} sm
    join scc_map rm
        on rm.tool_run_pk = sm.run_pk
),
lizard_files as (
    select
        lm.run_pk,
        rm.collection_run_id,
        rm.layout_run_pk,
        rm.semgrep_run_pk,
        rm.symbol_run_pk,
        lm.file_id,
        lm.nloc,
        lm.total_ccn as lizard_total_ccn,
        lm.avg_ccn,
        lm.max_ccn
    from {{ source('lz', 'lz_lizard_file_metrics') }} lm
    join lizard_map rm
        on rm.tool_run_pk = lm.run_pk
),
symbol_files as (
    select
        sm.run_pk,
        sm.file_id,
        sm.symbol_count,
        sm.function_count,
        sm.class_count
    from {{ ref('stg_symbols_file_metrics') }} sm
),
dotcover_files as (
    select
        dcf.run_pk,
        dm.collection_run_id,
        dm.layout_run_pk,
        dcf.file_id,
        dcf.type_count,
        dcf.covered_statements,
        dcf.total_statements,
        dcf.statement_coverage_pct
    from {{ ref('stg_dotcover_file_metrics') }} dcf
    join dotcover_map dm on dm.tool_run_pk = dcf.run_pk
),
roslyn_files as (
    select
        rf.run_pk,
        rm.collection_run_id,
        rm.layout_run_pk,
        rf.file_id,
        rf.violation_count,
        rf.severity_critical,
        rf.severity_high,
        rf.severity_medium,
        rf.severity_low,
        rf.severity_info,
        rf.severity_high_plus
    from {{ ref('stg_roslyn_file_metrics') }} rf
    join roslyn_map rm on rm.tool_run_pk = rf.run_pk
),
semgrep_files as (
    select
        sf.run_pk,
        sf.file_id,
        sf.smell_count,
        sf.severity_critical,
        sf.severity_high,
        sf.severity_medium,
        sf.severity_low,
        sf.severity_info,
        sf.severity_high_plus
    from {{ ref('stg_semgrep_file_metrics') }} sf
),
devskim_files as (
    select
        df.run_pk,
        dm.collection_run_id,
        dm.layout_run_pk,
        df.file_id,
        df.issue_count,
        df.severity_critical,
        df.severity_high,
        df.severity_medium,
        df.severity_low,
        df.severity_high_plus
    from {{ ref('stg_devskim_file_metrics') }} df
    join devskim_map dm on dm.tool_run_pk = df.run_pk
),
sonarqube_files as (
    select
        sf.run_pk,
        sm.collection_run_id,
        sm.layout_run_pk,
        sf.file_id,
        sf.issue_count,
        sf.type_bug,
        sf.type_vulnerability,
        sf.type_code_smell,
        sf.type_security_hotspot,
        sf.severity_blocker,
        sf.severity_critical,
        sf.severity_major,
        sf.severity_minor,
        sf.severity_info,
        sf.severity_high_plus,
        sf.cognitive_complexity,
        sf.duplicated_lines,
        sf.duplicated_lines_density
    from {{ ref('stg_sonarqube_file_metrics') }} sf
    join sonarqube_map sm on sm.tool_run_pk = sf.run_pk
),
gitleaks_files as (
    select
        gm.layout_run_pk,
        gs.run_pk,
        gs.file_id,
        gs.secret_count,
        gs.severity_critical,
        gs.severity_high,
        gs.severity_medium,
        gs.severity_low,
        gs.severity_high_plus,
        gs.secrets_in_head,
        gs.secrets_in_history,
        gs.unique_rule_count,
        gs.avg_entropy,
        gs.max_entropy
    from {{ ref('stg_gitleaks_secrets') }} gs
    join gitleaks_map gm
        on gm.tool_run_pk = gs.run_pk
),
trivy_files as (
    select
        tm.layout_run_pk,
        tf.run_pk,
        tf.file_id,
        tf.vulnerability_count,
        tf.vuln_critical,
        tf.vuln_high,
        tf.vuln_medium,
        tf.vuln_low,
        tf.iac_misconfig_count,
        tf.iac_critical,
        tf.iac_high,
        tf.iac_medium,
        tf.iac_low,
        tf.total_finding_count,
        tf.total_critical,
        tf.total_high,
        tf.severity_high_plus
    from {{ ref('stg_trivy_file_metrics') }} tf
    join trivy_map tm
        on tm.tool_run_pk = tf.run_pk
),
call_files as (
    select
        cm.run_pk,
        cm.file_id,
        cm.call_count
    from {{ ref('stg_symbol_calls_file_metrics') }} cm
),
import_files as (
    select
        im.run_pk,
        im.file_id,
        im.import_count
    from {{ ref('stg_file_imports_file_metrics') }} im
),
combined as (
    select
        coalesce(scc.run_pk, lizard.run_pk) as run_pk,
        coalesce(scc.collection_run_id, lizard.collection_run_id) as collection_run_id,
        scc.run_pk as scc_run_pk,
        lizard.run_pk as lizard_run_pk,
        coalesce(scc.semgrep_run_pk, lizard.semgrep_run_pk) as semgrep_run_pk,
        coalesce(scc.symbol_run_pk, lizard.symbol_run_pk) as symbol_run_pk,
        coalesce(scc.layout_run_pk, lizard.layout_run_pk) as layout_run_pk,
        coalesce(scc.file_id, lizard.file_id) as file_id,
        scc.lines_total,
        scc.code_lines,
        scc.comment_lines,
        scc.blank_lines,
        scc.complexity as scc_complexity,
        lizard.nloc,
        lizard.lizard_total_ccn,
        lizard.avg_ccn,
        lizard.max_ccn,
        concat_ws(
            ',',
            case when scc.run_pk is not null then 'scc' end,
            case when lizard.run_pk is not null then 'lizard' end
        ) as sources
    from scc_files scc
    full outer join lizard_files lizard
        on lizard.layout_run_pk = scc.layout_run_pk
       and lizard.file_id = scc.file_id
)
select
    combined.run_pk,
    combined.collection_run_id,
    combined.scc_run_pk,
    combined.lizard_run_pk,
    combined.semgrep_run_pk,
    combined.symbol_run_pk as symbol_run_pk,
    dc.run_pk as dotcover_run_pk,
    combined.layout_run_pk,
    combined.file_id,
    lf.relative_path,
    lf.directory_id,
    combined.lines_total as loc_total,
    combined.code_lines as loc_code,
    combined.comment_lines as loc_comment,
    combined.blank_lines as loc_blank,
    combined.scc_complexity as complexity_total,
    combined.nloc,
    combined.lizard_total_ccn as complexity_total_ccn,
    combined.avg_ccn as complexity_avg,
    combined.max_ccn as complexity_max,
    sf.symbol_count,
    sf.function_count,
    sf.class_count,
    cf.call_count,
    imf.import_count,
    dc.type_count as coverage_type_count,
    dc.covered_statements as coverage_covered_statements,
    dc.total_statements as coverage_total_statements,
    dc.statement_coverage_pct as coverage_statement_pct,
    ros.run_pk as roslyn_run_pk,
    ros.violation_count as roslyn_violation_count,
    ros.severity_critical as roslyn_severity_critical,
    ros.severity_high as roslyn_severity_high,
    ros.severity_medium as roslyn_severity_medium,
    ros.severity_low as roslyn_severity_low,
    ros.severity_info as roslyn_severity_info,
    ros.severity_high_plus as roslyn_severity_high_plus,
    sg.smell_count as semgrep_smell_count,
    sg.severity_critical as semgrep_severity_critical,
    sg.severity_high as semgrep_severity_high,
    sg.severity_medium as semgrep_severity_medium,
    sg.severity_low as semgrep_severity_low,
    sg.severity_info as semgrep_severity_info,
    sg.severity_high_plus as semgrep_severity_high_plus,
    dsk.run_pk as devskim_run_pk,
    dsk.issue_count as devskim_issue_count,
    dsk.severity_critical as devskim_severity_critical,
    dsk.severity_high as devskim_severity_high,
    dsk.severity_medium as devskim_severity_medium,
    dsk.severity_low as devskim_severity_low,
    dsk.severity_high_plus as devskim_severity_high_plus,
    sq.run_pk as sonarqube_run_pk,
    sq.issue_count as sonarqube_issue_count,
    sq.type_bug as sonarqube_type_bug,
    sq.type_vulnerability as sonarqube_type_vulnerability,
    sq.type_code_smell as sonarqube_type_code_smell,
    sq.type_security_hotspot as sonarqube_type_security_hotspot,
    sq.severity_blocker as sonarqube_severity_blocker,
    sq.severity_critical as sonarqube_severity_critical,
    sq.severity_major as sonarqube_severity_major,
    sq.severity_minor as sonarqube_severity_minor,
    sq.severity_info as sonarqube_severity_info,
    sq.severity_high_plus as sonarqube_severity_high_plus,
    sq.cognitive_complexity as sonarqube_cognitive_complexity,
    sq.duplicated_lines as sonarqube_duplicated_lines,
    sq.duplicated_lines_density as sonarqube_duplicated_lines_density,
    -- Gitleaks metrics
    gl.run_pk as gitleaks_run_pk,
    gl.secret_count as gitleaks_secret_count,
    gl.severity_critical as gitleaks_severity_critical,
    gl.severity_high as gitleaks_severity_high,
    gl.severity_medium as gitleaks_severity_medium,
    gl.severity_low as gitleaks_severity_low,
    gl.severity_high_plus as gitleaks_severity_high_plus,
    gl.secrets_in_head as gitleaks_secrets_in_head,
    gl.secrets_in_history as gitleaks_secrets_in_history,
    gl.unique_rule_count as gitleaks_unique_rule_count,
    gl.avg_entropy as gitleaks_avg_entropy,
    gl.max_entropy as gitleaks_max_entropy,
    -- Trivy metrics
    tv.run_pk as trivy_run_pk,
    tv.vulnerability_count as trivy_vulnerability_count,
    tv.vuln_critical as trivy_vuln_critical,
    tv.vuln_high as trivy_vuln_high,
    tv.vuln_medium as trivy_vuln_medium,
    tv.vuln_low as trivy_vuln_low,
    tv.iac_misconfig_count as trivy_iac_misconfig_count,
    tv.iac_critical as trivy_iac_critical,
    tv.iac_high as trivy_iac_high,
    tv.iac_medium as trivy_iac_medium,
    tv.iac_low as trivy_iac_low,
    tv.total_finding_count as trivy_total_finding_count,
    tv.severity_high_plus as trivy_severity_high_plus,
    concat_ws(
        ',',
        combined.sources,
        case when sf.run_pk is not null then 'symbol-scanner' end,
        case when dc.run_pk is not null then 'dotcover' end,
        case when ros.run_pk is not null then 'roslyn-analyzers' end,
        case when sg.run_pk is not null then 'semgrep' end,
        case when dsk.run_pk is not null then 'devskim' end,
        case when sq.run_pk is not null then 'sonarqube' end,
        case when gl.run_pk is not null then 'gitleaks' end,
        case when tv.run_pk is not null then 'trivy' end
    ) as sources
from combined
join {{ source('lz', 'lz_layout_files') }} lf
    on lf.run_pk = combined.layout_run_pk
   and lf.file_id = combined.file_id
left join symbol_files sf
    on sf.run_pk = combined.symbol_run_pk
   and sf.file_id = combined.file_id
left join call_files cf
    on cf.run_pk = combined.symbol_run_pk
   and cf.file_id = combined.file_id
left join import_files imf
    on imf.run_pk = combined.symbol_run_pk
   and imf.file_id = combined.file_id
left join dotcover_files dc
    on dc.layout_run_pk = combined.layout_run_pk
   and dc.file_id = combined.file_id
left join roslyn_files ros
    on ros.layout_run_pk = combined.layout_run_pk
   and ros.file_id = combined.file_id
left join semgrep_files sg
    on sg.run_pk = combined.semgrep_run_pk
   and sg.file_id = combined.file_id
left join devskim_files dsk
    on dsk.layout_run_pk = combined.layout_run_pk
   and dsk.file_id = combined.file_id
left join sonarqube_files sq
    on sq.layout_run_pk = combined.layout_run_pk
   and sq.file_id = combined.file_id
left join gitleaks_files gl
    on gl.layout_run_pk = combined.layout_run_pk
   and gl.file_id = combined.file_id
left join trivy_files tv
    on tv.layout_run_pk = combined.layout_run_pk
   and tv.file_id = combined.file_id
