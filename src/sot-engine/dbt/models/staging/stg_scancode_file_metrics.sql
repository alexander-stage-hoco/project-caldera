-- Aggregates lz_scancode_file_licenses to file-level metrics
-- Produces one row per file with license counts by category and match type

with licenses as (
    select
        run_pk,
        file_id,
        directory_id,
        relative_path,
        category,
        match_type,
        confidence
    from {{ ref('stg_lz_scancode_file_licenses') }}
),
file_metrics as (
    select
        run_pk,
        file_id,
        directory_id,
        min(relative_path) as relative_path,
        count(*) as license_count,
        -- Category counts
        count(case when category = 'copyleft' then 1 end) as cat_copyleft,
        count(case when category = 'permissive' then 1 end) as cat_permissive,
        count(case when category = 'weak-copyleft' then 1 end) as cat_weak_copyleft,
        count(case when category = 'unknown' then 1 end) as cat_unknown,
        -- Match type counts
        count(case when match_type = 'file' then 1 end) as match_file,
        count(case when match_type = 'header' then 1 end) as match_header,
        count(case when match_type = 'spdx' then 1 end) as match_spdx,
        -- Confidence
        avg(confidence) as avg_confidence
    from licenses
    group by run_pk, file_id, directory_id
)
select * from file_metrics
