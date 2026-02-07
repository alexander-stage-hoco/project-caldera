-- PMD-CPD clone hotspots: identify most impactful code clones for refactoring prioritization
-- Risk levels based on size, occurrence count, and cross-file spread

with clone_files as (
    -- Aggregate file/directory info per clone
    select
        run_pk,
        clone_id,
        count(distinct file_id) as files_affected,
        count(distinct directory_id) as directories_affected
    from {{ ref('stg_lz_pmd_cpd_occurrences') }}
    group by run_pk, clone_id
),
clone_metrics as (
    select
        d.run_pk,
        d.clone_id,
        d.lines,
        d.tokens,
        d.occurrence_count,
        d.is_cross_file,
        cf.files_affected,
        cf.directories_affected,
        -- Derived metrics
        d.lines * d.occurrence_count as total_duplicated_lines,
        round(d.tokens::double / nullif(d.lines, 0), 2) as token_density,
        -- Impact score: size × occurrences × spread factor
        (d.lines * d.occurrence_count *
         case when d.is_cross_file then 1.5 else 1.0 end) as impact_score
    from {{ ref('stg_lz_pmd_cpd_duplications') }} d
    left join clone_files cf on d.run_pk = cf.run_pk and d.clone_id = cf.clone_id
),
ranked_clones as (
    select
        *,
        row_number() over (partition by run_pk order by lines desc) as size_rank,
        row_number() over (partition by run_pk order by occurrence_count desc, lines desc) as occurrence_rank,
        row_number() over (partition by run_pk order by total_duplicated_lines desc) as impact_rank,
        row_number() over (partition by run_pk order by files_affected desc, lines desc) as spread_rank,
        -- Risk level classification
        case
            when lines >= 100 and is_cross_file then 'critical'
            when lines >= 100 or (lines >= 50 and is_cross_file) or occurrence_count >= 5 then 'high'
            when lines >= 20 or is_cross_file or occurrence_count >= 3 then 'medium'
            else 'low'
        end as risk_level
    from clone_metrics
)
select
    run_pk,
    clone_id,
    lines,
    tokens,
    occurrence_count,
    is_cross_file,
    files_affected,
    directories_affected,
    total_duplicated_lines,
    token_density,
    impact_score,
    size_rank,
    occurrence_rank,
    impact_rank,
    spread_rank,
    risk_level
from ranked_clones
order by run_pk, impact_score desc
