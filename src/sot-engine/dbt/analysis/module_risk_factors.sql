{% set run_pk = var('run_pk') %}
{% set limit_rows = var('limit', 30) %}

-- Module risk factors based on inequality patterns across all 5 tools
-- Identifies directories with multiple risk signals

-- Resolve tool-specific run_pks from collection
with run_map as (
    select
        tr_anchor.run_pk as scc_run_pk,
        tr_lizard.run_pk as lizard_run_pk,
        tr_semgrep.run_pk as semgrep_run_pk,
        tr_roslyn.run_pk as roslyn_run_pk,
        tr_sonarqube.run_pk as sonarqube_run_pk
    from {{ source('lz', 'lz_tool_runs') }} tr_anchor
    left join {{ source('lz', 'lz_tool_runs') }} tr_lizard
        on tr_lizard.collection_run_id = tr_anchor.collection_run_id
        and tr_lizard.tool_name = 'lizard'
    left join {{ source('lz', 'lz_tool_runs') }} tr_semgrep
        on tr_semgrep.collection_run_id = tr_anchor.collection_run_id
        and tr_semgrep.tool_name = 'semgrep'
    left join {{ source('lz', 'lz_tool_runs') }} tr_roslyn
        on tr_roslyn.collection_run_id = tr_anchor.collection_run_id
        and tr_roslyn.tool_name in ('roslyn', 'roslyn-analyzers')
    left join {{ source('lz', 'lz_tool_runs') }} tr_sonarqube
        on tr_sonarqube.collection_run_id = tr_anchor.collection_run_id
        and tr_sonarqube.tool_name = 'sonarqube'
    where tr_anchor.tool_name = 'scc'
      and tr_anchor.run_pk = {{ run_pk }}
),
scc_risk as (
    select
        directory_path,
        max(case when metric = 'lines_total' then gini_value end) as loc_gini,
        max(case when metric = 'lines_total' then top_20_pct_share end) as loc_top20,
        max(case when metric = 'lines_total' then p95_value end) as loc_p95,
        max(case when metric = 'lines_total' then value_count end) as file_count
    from {{ ref('rollup_scc_directory_recursive_distributions') }}
    where run_pk = (select scc_run_pk from run_map)
      and metric = 'lines_total'
    group by directory_path
),
lizard_risk as (
    select
        directory_path,
        max(case when metric = 'total_ccn' then gini_value end) as ccn_gini,
        max(case when metric = 'total_ccn' then top_20_pct_share end) as ccn_top20,
        max(case when metric = 'total_ccn' then p95_value end) as ccn_p95
    from {{ ref('rollup_lizard_directory_recursive_distributions') }}
    where run_pk = (select lizard_run_pk from run_map)
      and metric = 'total_ccn'
    group by directory_path
),
semgrep_risk as (
    select
        directory_path,
        max(gini_value) as smell_gini,
        max(top_20_pct_share) as smell_top20,
        max(p95_value) as smell_p95
    from {{ ref('rollup_semgrep_directory_recursive_distributions') }}
    where run_pk = (select semgrep_run_pk from run_map)
      and metric = 'smell_count'
    group by directory_path
),
roslyn_risk as (
    select
        directory_path,
        max(gini_value) as violation_gini,
        max(top_20_pct_share) as violation_top20,
        max(p95_value) as violation_p95
    from {{ ref('rollup_roslyn_directory_recursive_distributions') }}
    where run_pk = (select roslyn_run_pk from run_map)
      and metric = 'violation_count'
    group by directory_path
),
sonarqube_risk as (
    select
        directory_path,
        max(gini_value) as issue_gini,
        max(top_20_pct_share) as issue_top20,
        max(p95_value) as issue_p95
    from {{ ref('rollup_sonarqube_directory_recursive_distributions') }}
    where run_pk = (select sonarqube_run_pk from run_map)
      and metric = 'issue_count'
    group by directory_path
),
combined as (
    select
        s.directory_path,
        s.file_count,
        s.loc_gini,
        s.loc_top20,
        s.loc_p95,
        l.ccn_gini,
        l.ccn_top20,
        l.ccn_p95,
        sm.smell_gini,
        sm.smell_top20,
        sm.smell_p95,
        r.violation_gini,
        r.violation_top20,
        r.violation_p95,
        sq.issue_gini,
        sq.issue_top20,
        sq.issue_p95,
        -- Risk flags
        case when coalesce(s.loc_gini, 0) >= 0.5 then 1 else 0 end as high_loc_inequality,
        case when coalesce(l.ccn_gini, 0) >= 0.5 then 1 else 0 end as high_ccn_inequality,
        case when coalesce(sm.smell_gini, 0) >= 0.5 then 1 else 0 end as high_smell_inequality,
        case when coalesce(r.violation_gini, 0) >= 0.5 then 1 else 0 end as high_violation_inequality,
        case when coalesce(sq.issue_gini, 0) >= 0.5 then 1 else 0 end as high_issue_inequality,
        case when coalesce(s.loc_top20, 0) >= 0.7 then 1 else 0 end as concentrated_loc,
        case when coalesce(l.ccn_top20, 0) >= 0.7 then 1 else 0 end as concentrated_ccn,
        case when coalesce(sm.smell_top20, 0) >= 0.7 then 1 else 0 end as concentrated_smells,
        case when coalesce(r.violation_top20, 0) >= 0.7 then 1 else 0 end as concentrated_violations,
        case when coalesce(sq.issue_top20, 0) >= 0.7 then 1 else 0 end as concentrated_issues
    from scc_risk s
    left join lizard_risk l on l.directory_path = s.directory_path
    left join semgrep_risk sm on sm.directory_path = s.directory_path
    left join roslyn_risk r on r.directory_path = s.directory_path
    left join sonarqube_risk sq on sq.directory_path = s.directory_path
    where s.file_count >= 3
),
risk_scored as (
    select
        *,
        -- Total risk flags (max 10)
        (high_loc_inequality + high_ccn_inequality + high_smell_inequality
         + high_violation_inequality + high_issue_inequality
         + concentrated_loc + concentrated_ccn + concentrated_smells
         + concentrated_violations + concentrated_issues) as risk_flag_count,
        -- Weighted risk score
        (coalesce(loc_gini, 0) * 0.2 + coalesce(ccn_gini, 0) * 0.3
         + coalesce(smell_gini, 0) * 0.2 + coalesce(violation_gini, 0) * 0.15
         + coalesce(issue_gini, 0) * 0.15) as weighted_risk_score
    from combined
),
ranked as (
    select
        *,
        row_number() over (order by risk_flag_count desc, weighted_risk_score desc, file_count desc) as risk_rank
    from risk_scored
    where risk_flag_count >= 1  -- At least one risk flag
)
select
    directory_path,
    file_count,
    risk_flag_count,
    round(weighted_risk_score, 3) as weighted_risk_score,
    case
        when risk_flag_count >= 6 then 'critical'
        when risk_flag_count >= 4 then 'high'
        when risk_flag_count >= 2 then 'moderate'
        else 'low'
    end as risk_level,
    -- Individual ginis
    round(loc_gini, 3) as loc_gini,
    round(ccn_gini, 3) as ccn_gini,
    round(smell_gini, 3) as smell_gini,
    round(violation_gini, 3) as violation_gini,
    round(issue_gini, 3) as issue_gini,
    -- Concentration flags as comma-separated list
    concat_ws(', ',
        case when high_loc_inequality = 1 then 'high_loc_ineq' end,
        case when high_ccn_inequality = 1 then 'high_ccn_ineq' end,
        case when high_smell_inequality = 1 then 'high_smell_ineq' end,
        case when high_violation_inequality = 1 then 'high_violation_ineq' end,
        case when high_issue_inequality = 1 then 'high_issue_ineq' end,
        case when concentrated_loc = 1 then 'conc_loc' end,
        case when concentrated_ccn = 1 then 'conc_ccn' end,
        case when concentrated_smells = 1 then 'conc_smells' end,
        case when concentrated_violations = 1 then 'conc_violations' end,
        case when concentrated_issues = 1 then 'conc_issues' end
    ) as risk_flags,
    risk_rank
from ranked
where risk_rank <= {{ limit_rows }}
order by risk_rank
