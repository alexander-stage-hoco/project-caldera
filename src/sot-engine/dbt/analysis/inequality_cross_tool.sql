{% set run_pk = var('run_pk') %}
{% set limit_rows = var('limit', 50) %}

-- Per-directory cross-tool inequality view
-- Shows all 5 Gini values per directory with pattern classification

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
all_ginis as (
    select
        directory_path,
        max(case when tool = 'scc' and metric = 'lines_total' then gini end) as loc_gini,
        max(case when tool = 'lizard' and metric = 'total_ccn' then gini end) as ccn_gini,
        max(case when tool = 'semgrep' and metric = 'smell_count' then gini end) as smell_gini,
        max(case when tool = 'roslyn' and metric = 'violation_count' then gini end) as violation_gini,
        max(case when tool = 'sonarqube' and metric = 'issue_count' then gini end) as issue_gini,
        max(case when tool = 'scc' then file_count end) as file_count
    from (
        select
            'scc' as tool,
            directory_path,
            metric,
            gini_value as gini,
            value_count as file_count
        from {{ ref('rollup_scc_directory_recursive_distributions') }}
        where run_pk = (select scc_run_pk from run_map)
          and metric = 'lines_total'
          and value_count >= 3
        union all
        select
            'lizard' as tool,
            directory_path,
            metric,
            gini_value as gini,
            value_count as file_count
        from {{ ref('rollup_lizard_directory_recursive_distributions') }}
        where run_pk = (select lizard_run_pk from run_map)
          and metric = 'total_ccn'
          and value_count >= 3
        union all
        select
            'semgrep' as tool,
            directory_path,
            metric,
            gini_value as gini,
            value_count as file_count
        from {{ ref('rollup_semgrep_directory_recursive_distributions') }}
        where run_pk = (select semgrep_run_pk from run_map)
          and metric = 'smell_count'
          and value_count >= 3
        union all
        select
            'roslyn' as tool,
            directory_path,
            metric,
            gini_value as gini,
            value_count as file_count
        from {{ ref('rollup_roslyn_directory_recursive_distributions') }}
        where run_pk = (select roslyn_run_pk from run_map)
          and metric = 'violation_count'
          and value_count >= 3
        union all
        select
            'sonarqube' as tool,
            directory_path,
            metric,
            gini_value as gini,
            value_count as file_count
        from {{ ref('rollup_sonarqube_directory_recursive_distributions') }}
        where run_pk = (select sonarqube_run_pk from run_map)
          and metric = 'issue_count'
          and value_count >= 3
    ) combined
    group by directory_path
),
classified as (
    select
        directory_path,
        file_count,
        loc_gini,
        ccn_gini,
        smell_gini,
        violation_gini,
        issue_gini,
        -- Count high inequality dimensions
        (case when coalesce(loc_gini, 0) >= 0.5 then 1 else 0 end
         + case when coalesce(ccn_gini, 0) >= 0.5 then 1 else 0 end
         + case when coalesce(smell_gini, 0) >= 0.5 then 1 else 0 end
         + case when coalesce(violation_gini, 0) >= 0.5 then 1 else 0 end
         + case when coalesce(issue_gini, 0) >= 0.5 then 1 else 0 end) as high_inequality_count,
        -- Max gini for sorting
        greatest(
            coalesce(loc_gini, 0),
            coalesce(ccn_gini, 0),
            coalesce(smell_gini, 0),
            coalesce(violation_gini, 0),
            coalesce(issue_gini, 0)
        ) as max_gini,
        -- Pattern classification
        case
            when (case when coalesce(loc_gini, 0) >= 0.5 then 1 else 0 end
                  + case when coalesce(ccn_gini, 0) >= 0.5 then 1 else 0 end
                  + case when coalesce(smell_gini, 0) >= 0.5 then 1 else 0 end
                  + case when coalesce(violation_gini, 0) >= 0.5 then 1 else 0 end
                  + case when coalesce(issue_gini, 0) >= 0.5 then 1 else 0 end) >= 3
                then 'multi_concentrated'
            when coalesce(loc_gini, 0) >= 0.5 and coalesce(ccn_gini, 0) < 0.3
                then 'size_only'
            when coalesce(loc_gini, 0) < 0.3 and coalesce(ccn_gini, 0) >= 0.5
                then 'complexity_only'
            when coalesce(smell_gini, 0) >= 0.5 and coalesce(loc_gini, 0) < 0.3 and coalesce(ccn_gini, 0) < 0.3
                then 'smell_only'
            when coalesce(violation_gini, 0) >= 0.5 and coalesce(loc_gini, 0) < 0.3
                then 'violation_only'
            when coalesce(issue_gini, 0) >= 0.5 and coalesce(loc_gini, 0) < 0.3
                then 'issue_only'
            when greatest(coalesce(loc_gini, 0), coalesce(ccn_gini, 0), coalesce(smell_gini, 0),
                         coalesce(violation_gini, 0), coalesce(issue_gini, 0)) < 0.3
                then 'balanced'
            else 'mixed'
        end as pattern
    from all_ginis
    where loc_gini is not null or ccn_gini is not null
)
select
    directory_path,
    file_count,
    round(loc_gini, 3) as loc_gini,
    round(ccn_gini, 3) as ccn_gini,
    round(smell_gini, 3) as smell_gini,
    round(violation_gini, 3) as violation_gini,
    round(issue_gini, 3) as issue_gini,
    high_inequality_count,
    round(max_gini, 3) as max_gini,
    pattern,
    row_number() over (order by max_gini desc, high_inequality_count desc, file_count desc) as rank_id
from classified
order by max_gini desc, high_inequality_count desc, file_count desc
limit {{ limit_rows }}
