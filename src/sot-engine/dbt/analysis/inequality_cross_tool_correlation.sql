{% set run_pk = var('run_pk') %}

-- Repo-level correlation matrix between tool Gini values
-- Calculates Pearson correlation coefficients across all directories

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
        max(case when tool = 'sonarqube' and metric = 'issue_count' then gini end) as issue_gini
    from (
        select
            'scc' as tool,
            directory_path,
            metric,
            gini_value as gini
        from {{ ref('rollup_scc_directory_recursive_distributions') }}
        where run_pk = (select scc_run_pk from run_map)
          and metric = 'lines_total'
          and value_count >= 3
        union all
        select
            'lizard' as tool,
            directory_path,
            metric,
            gini_value as gini
        from {{ ref('rollup_lizard_directory_recursive_distributions') }}
        where run_pk = (select lizard_run_pk from run_map)
          and metric = 'total_ccn'
          and value_count >= 3
        union all
        select
            'semgrep' as tool,
            directory_path,
            metric,
            gini_value as gini
        from {{ ref('rollup_semgrep_directory_recursive_distributions') }}
        where run_pk = (select semgrep_run_pk from run_map)
          and metric = 'smell_count'
          and value_count >= 3
        union all
        select
            'roslyn' as tool,
            directory_path,
            metric,
            gini_value as gini
        from {{ ref('rollup_roslyn_directory_recursive_distributions') }}
        where run_pk = (select roslyn_run_pk from run_map)
          and metric = 'violation_count'
          and value_count >= 3
        union all
        select
            'sonarqube' as tool,
            directory_path,
            metric,
            gini_value as gini
        from {{ ref('rollup_sonarqube_directory_recursive_distributions') }}
        where run_pk = (select sonarqube_run_pk from run_map)
          and metric = 'issue_count'
          and value_count >= 3
    ) combined
    group by directory_path
),
correlation_pairs as (
    select
        'loc_vs_ccn' as pair,
        'LOC Gini' as metric_a,
        'CCN Gini' as metric_b,
        corr(loc_gini, ccn_gini) as correlation,
        count(*) as sample_count
    from all_ginis
    where loc_gini is not null and ccn_gini is not null

    union all

    select
        'loc_vs_smell' as pair,
        'LOC Gini' as metric_a,
        'Smell Gini' as metric_b,
        corr(loc_gini, smell_gini) as correlation,
        count(*) as sample_count
    from all_ginis
    where loc_gini is not null and smell_gini is not null

    union all

    select
        'loc_vs_violation' as pair,
        'LOC Gini' as metric_a,
        'Violation Gini' as metric_b,
        corr(loc_gini, violation_gini) as correlation,
        count(*) as sample_count
    from all_ginis
    where loc_gini is not null and violation_gini is not null

    union all

    select
        'loc_vs_issue' as pair,
        'LOC Gini' as metric_a,
        'Issue Gini' as metric_b,
        corr(loc_gini, issue_gini) as correlation,
        count(*) as sample_count
    from all_ginis
    where loc_gini is not null and issue_gini is not null

    union all

    select
        'ccn_vs_smell' as pair,
        'CCN Gini' as metric_a,
        'Smell Gini' as metric_b,
        corr(ccn_gini, smell_gini) as correlation,
        count(*) as sample_count
    from all_ginis
    where ccn_gini is not null and smell_gini is not null

    union all

    select
        'ccn_vs_violation' as pair,
        'CCN Gini' as metric_a,
        'Violation Gini' as metric_b,
        corr(ccn_gini, violation_gini) as correlation,
        count(*) as sample_count
    from all_ginis
    where ccn_gini is not null and violation_gini is not null

    union all

    select
        'ccn_vs_issue' as pair,
        'CCN Gini' as metric_a,
        'Issue Gini' as metric_b,
        corr(ccn_gini, issue_gini) as correlation,
        count(*) as sample_count
    from all_ginis
    where ccn_gini is not null and issue_gini is not null

    union all

    select
        'smell_vs_violation' as pair,
        'Smell Gini' as metric_a,
        'Violation Gini' as metric_b,
        corr(smell_gini, violation_gini) as correlation,
        count(*) as sample_count
    from all_ginis
    where smell_gini is not null and violation_gini is not null

    union all

    select
        'smell_vs_issue' as pair,
        'Smell Gini' as metric_a,
        'Issue Gini' as metric_b,
        corr(smell_gini, issue_gini) as correlation,
        count(*) as sample_count
    from all_ginis
    where smell_gini is not null and issue_gini is not null

    union all

    select
        'violation_vs_issue' as pair,
        'Violation Gini' as metric_a,
        'Issue Gini' as metric_b,
        corr(violation_gini, issue_gini) as correlation,
        count(*) as sample_count
    from all_ginis
    where violation_gini is not null and issue_gini is not null
)
select
    pair,
    metric_a,
    metric_b,
    sample_count,
    round(correlation, 3) as correlation,
    case
        when abs(correlation) >= 0.7 then 'strong'
        when abs(correlation) >= 0.4 then 'moderate'
        else 'weak'
    end as strength,
    case
        when correlation >= 0 then 'positive'
        else 'negative'
    end as direction,
    case
        when correlation is null then 'insufficient_data'
        when abs(correlation) >= 0.7 then 'Highly correlated - tools agree on inequality patterns'
        when abs(correlation) >= 0.4 then 'Moderately correlated - partial agreement'
        else 'Weakly correlated - tools measure different aspects'
    end as interpretation
from correlation_pairs
where correlation is not null
order by abs(correlation) desc
