{{ 
  config(
    materialized = 'table'
  ) 
}}

select
  *
from {{ ref('RAW_OFFRE') }}
qualify
  row_number() over (
    partition by id_local
    order by date_created desc
  ) = 1
