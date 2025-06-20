{{ 
  config(
    materialized = 'incremental',
    unique_key   = ['id_offre','id_competence'],
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
  f.id_offre,
  c.id_competence
from c
left join f
  on c.id_local = f.id_local