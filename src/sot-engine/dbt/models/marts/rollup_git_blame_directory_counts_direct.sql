-- Git blame authorship counts per directory (direct - only files in that directory)

with blame_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'git-blame-scanner'
),
dir_files as (
    select
        br.run_pk,
        gbs.directory_id,
        ld.relative_path as directory_path,
        gbs.file_id,
        gbs.total_lines,
        gbs.unique_authors,
        gbs.top_author_pct,
        gbs.churn_30d,
        gbs.churn_90d,
        case when gbs.unique_authors = 1 then 1 else 0 end as is_single_author,
        case when gbs.top_author_pct >= 80 then 1 else 0 end as is_high_concentration,
        case when gbs.unique_authors = 1 and gbs.total_lines > 100 then 1 else 0 end as is_knowledge_silo,
        case when gbs.churn_90d = 0 then 1 else 0 end as is_stale
    from {{ source('lz', 'lz_git_blame_summary') }} gbs
    join blame_runs br
        on br.run_pk = gbs.run_pk
    join {{ source('lz', 'lz_layout_directories') }} ld
        on ld.run_pk = br.run_pk
        and ld.directory_id = gbs.directory_id
)
select
    run_pk,
    directory_id,
    directory_path,
    count(distinct file_id) as file_count,
    sum(total_lines) as total_lines,
    avg(unique_authors) as avg_unique_authors,
    max(unique_authors) as max_unique_authors,
    avg(top_author_pct) as avg_top_author_pct,
    sum(is_single_author) as single_author_files,
    sum(is_high_concentration) as high_concentration_files,
    sum(is_knowledge_silo) as knowledge_silo_count,
    sum(is_stale) as stale_file_count,
    sum(churn_30d) as total_churn_30d,
    sum(churn_90d) as total_churn_90d
from dir_files
group by run_pk, directory_id, directory_path
