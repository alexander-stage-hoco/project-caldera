-- Author concentration hotspots for bus factor and knowledge risk analysis
-- Risk levels: critical (50%+), high (25-50%), medium (10-25%), low (5-10%), minimal (<5%)
-- Bus factor: minimum authors needed for 50% code ownership

with authors as (
    select
        run_pk,
        author_name,
        author_email,
        surviving_loc,
        ownership_pct,
        insertions_total,
        deletions_total,
        commit_count,
        files_touched,
        collection_run_id,
        run_id,
        repo_id
    from {{ ref('stg_lz_git_fame_authors') }}
),
summary as (
    select
        run_pk,
        author_count,
        total_loc,
        hhi_index,
        bus_factor,
        top_author_pct,
        top_two_pct
    from {{ ref('stg_lz_git_fame_summary') }}
),
author_stats as (
    select
        run_pk,
        avg(ownership_pct) as ownership_avg,
        stddev(ownership_pct) as ownership_stddev,
        percentile_cont(0.50) within group (order by ownership_pct) as ownership_p50,
        percentile_cont(0.75) within group (order by ownership_pct) as ownership_p75,
        percentile_cont(0.90) within group (order by ownership_pct) as ownership_p90,
        percentile_cont(0.95) within group (order by ownership_pct) as ownership_p95,
        percentile_cont(0.99) within group (order by ownership_pct) as ownership_p99
    from authors
    group by run_pk
),
ranked_authors as (
    select
        a.*,
        s.author_count,
        s.total_loc,
        s.hhi_index,
        s.bus_factor,
        s.top_author_pct,
        s.top_two_pct,
        st.ownership_avg,
        st.ownership_stddev,
        st.ownership_p50,
        st.ownership_p75,
        st.ownership_p90,
        st.ownership_p95,
        st.ownership_p99,
        -- Rankings
        row_number() over (partition by a.run_pk order by a.ownership_pct desc) as ownership_rank,
        row_number() over (partition by a.run_pk order by a.commit_count desc) as commit_rank,
        row_number() over (partition by a.run_pk order by a.files_touched desc) as files_rank,
        -- Cumulative ownership for bus factor calculation
        sum(a.ownership_pct) over (partition by a.run_pk order by a.ownership_pct desc rows unbounded preceding) as cumulative_ownership_pct
    from authors a
    join summary s on s.run_pk = a.run_pk
    join author_stats st on st.run_pk = a.run_pk
),
enriched_authors as (
    select
        ra.*,
        -- Risk level based on individual ownership concentration
        case
            when ra.ownership_pct >= 50.0 then 'critical'
            when ra.ownership_pct >= 25.0 then 'high'
            when ra.ownership_pct >= 10.0 then 'medium'
            when ra.ownership_pct >= 5.0 then 'low'
            else 'minimal'
        end as risk_level,
        case
            when ra.ownership_pct >= 50.0 then 5
            when ra.ownership_pct >= 25.0 then 4
            when ra.ownership_pct >= 10.0 then 3
            when ra.ownership_pct >= 5.0 then 2
            else 1
        end as risk_level_numeric,
        -- Bus factor membership: is this author in the minimum set for 50% coverage?
        ra.cumulative_ownership_pct - ra.ownership_pct < 50.0 as is_bus_factor_member,
        -- Z-score for ownership
        case
            when ra.ownership_stddev > 0 then round((ra.ownership_pct - ra.ownership_avg) / ra.ownership_stddev, 2)
            else 0
        end as ownership_zscore,
        -- Relative position
        case
            when ra.ownership_pct >= ra.ownership_p99 then 'p99_outlier'
            when ra.ownership_pct >= ra.ownership_p95 then 'p95_outlier'
            when ra.ownership_pct >= ra.ownership_p90 then 'p90_outlier'
            when ra.ownership_pct >= ra.ownership_p75 then 'above_median'
            else 'normal'
        end as relative_position,
        -- Code retention ratio (how much code survives vs added)
        case
            when ra.insertions_total > 0 then round(ra.surviving_loc::double / ra.insertions_total, 4)
            else null
        end as code_retention_ratio,
        -- Churn ratio (deletions vs insertions)
        case
            when ra.insertions_total > 0 then round(ra.deletions_total::double / ra.insertions_total, 4)
            else null
        end as churn_ratio,
        ra.ownership_pct >= 10.0 as is_significant_contributor,
        ra.ownership_pct >= 25.0 as is_high_plus,
        ra.ownership_pct >= 50.0 as is_critical
    from ranked_authors ra
)
select
    run_pk,
    author_name,
    author_email,
    surviving_loc,
    ownership_pct,
    insertions_total,
    deletions_total,
    commit_count,
    files_touched,
    collection_run_id,
    run_id,
    repo_id,
    author_count,
    total_loc,
    hhi_index,
    bus_factor,
    top_author_pct,
    top_two_pct,
    ownership_rank,
    commit_rank,
    files_rank,
    cumulative_ownership_pct,
    risk_level,
    risk_level_numeric,
    is_bus_factor_member,
    ownership_zscore,
    relative_position,
    code_retention_ratio,
    churn_ratio,
    is_significant_contributor,
    is_high_plus,
    is_critical,
    ownership_avg as run_ownership_avg,
    ownership_stddev as run_ownership_stddev,
    ownership_p50 as run_ownership_p50,
    ownership_p75 as run_ownership_p75,
    ownership_p90 as run_ownership_p90,
    ownership_p95 as run_ownership_p95,
    ownership_p99 as run_ownership_p99
from enriched_authors
where ownership_pct >= 10.0 or is_bus_factor_member or ownership_zscore > 2.0
order by run_pk, ownership_pct desc
