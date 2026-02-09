-- Knowledge concentration risk analysis
-- Identifies files at risk due to knowledge silos or high ownership concentration

with blame_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'git-blame-scanner'
),
file_risk as (
    select
        br.run_pk,
        gbs.file_id,
        gbs.directory_id,
        gbs.relative_path,
        gbs.total_lines,
        gbs.unique_authors,
        gbs.top_author,
        gbs.top_author_pct,
        gbs.last_modified,
        gbs.churn_30d,
        gbs.churn_90d,
        -- Risk factors
        case when gbs.unique_authors = 1 then 1 else 0 end as is_single_author,
        case when gbs.top_author_pct >= 80 then 1 else 0 end as is_high_concentration,
        case when gbs.unique_authors = 1 and gbs.total_lines > 100 then 1 else 0 end as is_knowledge_silo,
        case when gbs.churn_90d = 0 then 1 else 0 end as is_stale,
        -- Calculate risk score (0-100)
        (
            -- Single author: +30 risk
            (case when gbs.unique_authors = 1 then 30 else 0 end) +
            -- High concentration (>80%): +25 risk
            (case when gbs.top_author_pct >= 80 then 25 else 0 end) +
            -- Large file (>100 LOC) with single author: +20 risk
            (case when gbs.unique_authors = 1 and gbs.total_lines > 100 then 20 else 0 end) +
            -- Stale (no commits in 90 days): +15 risk
            (case when gbs.churn_90d = 0 then 15 else 0 end) +
            -- Very large file (>500 LOC): +10 risk
            (case when gbs.total_lines > 500 then 10 else 0 end)
        ) as risk_score
    from {{ source('lz', 'lz_git_blame_summary') }} gbs
    join blame_runs br
        on br.run_pk = gbs.run_pk
)
select
    run_pk,
    file_id,
    directory_id,
    relative_path,
    total_lines,
    unique_authors,
    top_author,
    top_author_pct,
    last_modified,
    churn_30d,
    churn_90d,
    is_single_author,
    is_high_concentration,
    is_knowledge_silo,
    is_stale,
    risk_score,
    case
        when risk_score >= 70 then 'critical'
        when risk_score >= 50 then 'high'
        when risk_score >= 30 then 'medium'
        else 'low'
    end as risk_level
from file_risk
order by risk_score desc
