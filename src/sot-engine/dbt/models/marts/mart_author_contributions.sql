-- Author contributions: ranks and tiers authors by contribution level
-- Answers: "Who are the top contributors and what is their commitment level?"
-- Ranks authors by ownership and calculates commitment index

with authors as (
    select *
    from {{ ref('stg_lz_git_fame_authors') }}
),

-- Calculate author rankings within each run
ranked_authors as (
    select
        run_pk,
        collection_run_id,
        repo_id,
        branch,
        commit,
        author_name,
        author_email,
        surviving_loc,
        ownership_pct,
        insertions_total,
        deletions_total,
        commit_count,
        files_touched,
        -- Rank by ownership percentage
        row_number() over (
            partition by run_pk
            order by ownership_pct desc
        ) as contribution_rank,
        -- Cumulative ownership for tier calculation
        sum(ownership_pct) over (
            partition by run_pk
            order by ownership_pct desc
            rows between unbounded preceding and current row
        ) as cumulative_ownership_pct,
        -- Total authors in this run for percentile calculation
        count(*) over (partition by run_pk) as total_authors
    from authors
)

select
    run_pk,
    collection_run_id,
    repo_id,
    branch,
    commit,
    author_name,
    author_email,
    surviving_loc,
    ownership_pct,
    insertions_total,
    deletions_total,
    commit_count,
    files_touched,
    contribution_rank,
    -- Contribution tier based on cumulative ownership
    case
        when cumulative_ownership_pct - ownership_pct < 10.0 then 'top_10_pct'
        when cumulative_ownership_pct - ownership_pct < 25.0 then 'top_25_pct'
        when cumulative_ownership_pct - ownership_pct < 50.0 then 'top_50_pct'
        else 'bottom_50_pct'
    end as contribution_tier,
    -- Commitment index: ratio of surviving code to total insertions
    -- Higher = code that "sticks"; lower = code that gets replaced
    case
        when insertions_total > 0 then
            round(cast(surviving_loc as double) / cast(insertions_total as double), 4)
        else null
    end as commitment_index,
    -- Churn ratio: deletions / insertions
    -- Higher = more refactoring/cleanup activity
    case
        when insertions_total > 0 then
            round(cast(deletions_total as double) / cast(insertions_total as double), 4)
        else null
    end as churn_ratio,
    -- Files per commit
    case
        when commit_count > 0 then
            round(cast(files_touched as double) / cast(commit_count as double), 2)
        else null
    end as avg_files_per_commit
from ranked_authors
