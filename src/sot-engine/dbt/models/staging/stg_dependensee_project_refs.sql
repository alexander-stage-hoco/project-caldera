-- Staging model for dependensee project-to-project references
-- Maps which .NET projects reference other projects in the solution

SELECT
    run_pk,
    source_project_path,
    target_project_path
FROM {{ source('lz', 'lz_dependensee_project_refs') }}
