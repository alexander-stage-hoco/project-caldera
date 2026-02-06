-- Staging model for dependensee NuGet package references
-- Maps which NuGet packages each .NET project depends on

SELECT
    run_pk,
    project_path,
    package_name,
    package_version
FROM {{ source('lz', 'lz_dependensee_package_refs') }}
