-- Staging model for dependensee projects
-- Note: dependensee analyzes .NET project dependencies (project-level, not file-level)

SELECT
    run_pk,
    project_path,
    project_name,
    target_framework,
    project_reference_count,
    package_reference_count
FROM {{ source('lz', 'lz_dependensee_projects') }}
