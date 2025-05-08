{{ config(materialized = 'table') }}

with raw as (
  select * 
  from {{ source('RAW', 'RAW_OFFRE') }}
),
dim_rome as (
  select * 
  from {{ ref('DIM_ROMECODE') }}
)

select
  raw.id_local    as id_local,
  dim_rome.ID_ROME as id_rome
from raw
join dim_rome
  on lower(raw.CODE_ROME) = lower(dim_rome.CODE_ROME)
