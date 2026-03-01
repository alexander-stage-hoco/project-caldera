-- Evidence, claims, and risks summary per collection run.
-- Enables cross-run comparison of findings.

with evidence as (
    select
        collection_run_id,
        count(*) as total_evidence,
        count(case when category = 'complexity' then 1 end) as evidence_complexity,
        count(case when category = 'security' then 1 end) as evidence_security,
        count(case when category = 'coupling' then 1 end) as evidence_coupling,
        count(case when category = 'coverage' then 1 end) as evidence_coverage,
        count(case when category = 'ownership' then 1 end) as evidence_ownership,
        count(case when category = 'quality' then 1 end) as evidence_quality
    from {{ ref('stg_lz_evidence') }}
    group by collection_run_id
),

claims as (
    select
        collection_run_id,
        count(*) as total_claims,
        count(case when severity = 'critical' then 1 end) as claims_critical,
        count(case when severity = 'high' then 1 end) as claims_high,
        count(case when severity = 'medium' then 1 end) as claims_medium,
        count(case when severity = 'low' then 1 end) as claims_low
    from {{ ref('stg_lz_claims') }}
    group by collection_run_id
),

risks as (
    select
        collection_run_id,
        count(*) as total_risks,
        count(case when severity = 'critical' then 1 end) as risks_critical,
        count(case when severity = 'high' then 1 end) as risks_high,
        count(case when severity = 'medium' then 1 end) as risks_medium,
        count(case when severity = 'low' then 1 end) as risks_low
    from {{ ref('stg_lz_risks') }}
    group by collection_run_id
),

runs as (
    select collection_run_id, repo_id, commit, started_at
    from {{ source('lz', 'lz_collection_runs') }}
)

select
    r.collection_run_id,
    r.repo_id,
    r.commit,
    r.started_at,
    coalesce(e.total_evidence, 0) as total_evidence,
    coalesce(e.evidence_complexity, 0) as evidence_complexity,
    coalesce(e.evidence_security, 0) as evidence_security,
    coalesce(e.evidence_coupling, 0) as evidence_coupling,
    coalesce(e.evidence_coverage, 0) as evidence_coverage,
    coalesce(e.evidence_ownership, 0) as evidence_ownership,
    coalesce(e.evidence_quality, 0) as evidence_quality,
    coalesce(c.total_claims, 0) as total_claims,
    coalesce(c.claims_critical, 0) as claims_critical,
    coalesce(c.claims_high, 0) as claims_high,
    coalesce(c.claims_medium, 0) as claims_medium,
    coalesce(c.claims_low, 0) as claims_low,
    coalesce(ri.total_risks, 0) as total_risks,
    coalesce(ri.risks_critical, 0) as risks_critical,
    coalesce(ri.risks_high, 0) as risks_high,
    coalesce(ri.risks_medium, 0) as risks_medium,
    coalesce(ri.risks_low, 0) as risks_low
from runs r
left join evidence e on e.collection_run_id = r.collection_run_id
left join claims c on c.collection_run_id = r.collection_run_id
left join risks ri on ri.collection_run_id = r.collection_run_id
