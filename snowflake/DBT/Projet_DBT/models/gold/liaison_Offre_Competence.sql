{{ 
  config(
    materialized = 'incremental',
    unique_key   = ['id_local','id_competence'],
    on_schema_change = 'sync_all_columns'
  ) 
}}

with c as (
  select * from {{ ref('Match_Competence_sql') }}
),

f as (
  select * from {{ ref('fait_offre') }}
)

select
  c.id_local,
  c.id_competence
from c
left join f
  on c.id_local = f.id_local