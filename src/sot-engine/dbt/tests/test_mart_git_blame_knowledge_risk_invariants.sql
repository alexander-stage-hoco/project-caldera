select *
from {{ ref('mart_git_blame_knowledge_risk') }}
where
    -- risk_score bounded 0-100
    risk_score < 0
    or risk_score > 100

    -- risk_level thresholds match CASE logic
    or (risk_level = 'critical' and risk_score < 70)
    or (risk_level = 'high' and (risk_score < 50 or risk_score >= 70))
    or (risk_level = 'medium' and (risk_score < 30 or risk_score >= 50))
    or (risk_level = 'low' and risk_score >= 30)

    -- top_author_pct bounded 0-100
    or top_author_pct < 0
    or top_author_pct > 100

    -- is_knowledge_silo implies is_single_author
    or (is_knowledge_silo = 1 and is_single_author = 0)

    -- is_high_concentration iff top_author_pct >= 80
    or (is_high_concentration = 1 and top_author_pct < 80)
    or (is_high_concentration = 0 and top_author_pct >= 80)

    -- is_stale iff churn_90d = 0
    or (is_stale = 1 and churn_90d != 0)
    or (is_stale = 0 and churn_90d = 0)

    -- Non-negative counts and bounds
    or unique_authors < 1
    or total_lines < 0
    or churn_30d < 0
    or churn_90d < 0
