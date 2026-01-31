select *
from {{ ref('unified_file_metrics') }}
where loc_total < 0
   or loc_code < 0
   or loc_comment < 0
   or loc_blank < 0
   or complexity_total < 0
   or complexity_total_ccn < 0
   or complexity_avg < 0
   or complexity_max < 0
   or nloc < 0
