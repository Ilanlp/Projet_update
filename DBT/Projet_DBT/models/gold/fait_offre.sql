{{ 
  config(
    materialized = 'incremental',
    unique_key   = 'id_local',
    on_schema_change = 'append_new_columns'
  ) 
}}

with raw as (
    select *
    from {{ ref('raw_offre_clean') }}
    where date_extraction::date = current_date
),
source as (

  select
    raw.id_local,
    contrat.id_contrat,
    domaine.id_domaine,
    lieu.id_lieu,
    date_created.id_date_created    as id_date_creation,
    date_updated.id_date_updated    as id_date_modification,
    entreprise.id_entreprise,
    teletravail.id_teletravail,
    seniorite.id_seniorite,
    rome.id_rome
  from raw         as raw
  left join {{ ref('Match_Lieu_py') }}       as lieu
    on raw.id_local = lieu.id_local
  left join {{ ref('Match_Contrat_py') }}    as contrat
    on raw.id_local = contrat.id_local
  left join {{ ref('Match_Date_py') }}       as date_created
    on raw.id_local = date_created.id_local
  left join {{ ref('Match_Date_py') }}       as date_updated
    on raw.id_local = date_updated.id_local
  left join {{ ref('Match_Entreprise_py') }} as entreprise
    on raw.id_local = entreprise.id_local
  left join {{ ref('Match_Seniorite_py') }}  as seniorite
    on raw.id_local = seniorite.id_local
  left join {{ ref('Match_Teletravail_py') }} as teletravail
    on raw.id_local = teletravail.id_local
  left join {{ ref('Match_Domaine_sql') }}   as domaine
    on raw.id_local = domaine.id_local
  left join {{ ref('Match_Rome') }}       as rome
    on raw.id_local = rome.id_local

)

select
    id_local,
    id_contrat,
    id_domaine,
    id_lieu,
    id_date_creation,
    id_date_modification,
    id_entreprise,
    id_teletravail,
    id_seniorite,
    id_rome
from source
