select *
from {{ ref('unified_run_summary') }}
where total_files < 0
   or total_loc < 0
   or total_code < 0
   or total_comment < 0
   or total_blank < 0
   or total_ccn < 0
   or avg_ccn < 0
   or max_ccn < 0
   or avg_nloc < 0
   or max_ccn < avg_ccn
