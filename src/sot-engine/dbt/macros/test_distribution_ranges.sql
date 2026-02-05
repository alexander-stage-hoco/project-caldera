{% macro test_distribution_ranges(model_name) %}
{#
    Tests that distribution statistics are within valid ranges.

    Args:
        model_name: The name of the distribution model to test
#}

select *
from {{ ref(model_name) }}
where value_count <= 0
   or min_value > max_value
   or avg_value < min_value - 1e-9
   or avg_value > max_value + 1e-9
   or (p25_value is not null and p50_value is not null and p25_value > p50_value)
   or (p50_value is not null and p75_value is not null and p50_value > p75_value)
   or (p75_value is not null and p90_value is not null and p75_value > p90_value)
   or (p90_value is not null and p95_value is not null and p90_value > p95_value)
   or (p95_value is not null and p99_value is not null and p95_value > p99_value)
   or (median_value is not null and p50_value is not null and median_value != p50_value)
   or (cv_value is not null and cv_value < 0)
   or (iqr_value is not null and iqr_value < 0)
   or gini_value < 0
   or gini_value > 1
   or hoover_value < 0
   or hoover_value > 1
   or top_10_pct_share < 0
   or top_10_pct_share > 1
   or top_20_pct_share < 0
   or top_20_pct_share > 1
   or bottom_50_pct_share < 0
   or bottom_50_pct_share > 1
   or palma_value < 0

{% endmacro %}
