{{ config(
    materialized='table'
) }}

with ranked as (
    select *,
           row_number() over (
               partition by id_local
               order by date_extraction, id_offre desc
           ) as rn
    from {{ source('RAW', 'RAW_OFFRE') }}
)

select *
from ranked
where rn = 1