-- Authorship risk: team health assessment view
-- Answers: "What is the knowledge concentration risk for this repository?"
-- Provides actionable risk classifications for team health monitoring

with git_fame as (
    select *
    from {{ ref('stg_lz_git_fame_summary') }}
),

run_meta as (
    select
        run_pk,
        collection_run_id,
        run_id
    from {{ source('lz', 'lz_tool_runs') }}
)

select
    gf.run_pk,
    gf.collection_run_id,
    rm.run_id,
    gf.repo_id,
    gf.branch,
    gf.commit,
    -- Core metrics
    gf.author_count,
    gf.total_loc,
    gf.hhi_index,
    gf.bus_factor,
    gf.top_author_pct,
    gf.top_two_pct,
    -- Concentration classification (based on HHI)
    -- HHI: 0 = perfectly distributed, 1 = single author owns everything
    case
        when gf.hhi_index >= 0.5 then 'highly_concentrated'
        when gf.hhi_index >= 0.25 then 'moderately_concentrated'
        when gf.hhi_index >= 0.15 then 'slightly_concentrated'
        else 'well_distributed'
    end as concentration_level,
    -- Bus factor assessment
    case
        when gf.bus_factor = 0 then 'no_data'
        when gf.bus_factor = 1 then 'critical'
        when gf.bus_factor = 2 then 'at_risk'
        when gf.bus_factor <= 3 then 'moderate'
        else 'healthy'
    end as bus_factor_assessment,
    -- Single author risk flag
    gf.top_author_pct >= 80.0 as single_author_risk,
    -- Top-two dominance flag (two authors control 80%+)
    gf.top_two_pct >= 80.0 as top_two_dominance,
    -- Team health grade (A-F)
    case
        -- F: Critical - single author dominance or bus factor 1
        when gf.bus_factor <= 1 or gf.top_author_pct >= 80.0 then 'F'
        -- D: Poor - bus factor 2 or very high concentration
        when gf.bus_factor = 2 or gf.hhi_index >= 0.5 then 'D'
        -- C: Fair - bus factor 3 or high concentration
        when gf.bus_factor = 3 or gf.hhi_index >= 0.25 then 'C'
        -- B: Good - bus factor 4+ with moderate concentration
        when gf.bus_factor >= 4 and gf.hhi_index < 0.25 then 'B'
        -- A: Excellent - bus factor 5+ with low concentration
        when gf.bus_factor >= 5 and gf.hhi_index < 0.15 then 'A'
        else 'C'  -- Default to fair
    end as team_health_grade,
    -- Recommended actions
    case
        when gf.bus_factor <= 1 then 'Immediate knowledge transfer required - single point of failure'
        when gf.top_author_pct >= 80.0 then 'Plan succession - dominant author controls most code'
        when gf.bus_factor = 2 then 'Increase code review pairing - low redundancy'
        when gf.hhi_index >= 0.5 then 'Distribute ownership - high concentration detected'
        when gf.hhi_index >= 0.25 then 'Monitor contribution balance'
        else 'No immediate action required'
    end as recommended_action
from git_fame gf
join run_meta rm on gf.run_pk = rm.run_pk
