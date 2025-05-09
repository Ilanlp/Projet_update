{{ config(materialized='ephemeral',tags=['sql']) }}

{% set transformation_query %}

  INSERT INTO {{ source('dim_tables', 'DIM_CANDIDAT') }} (
    id_candidat,
    nom,
    prenom,
    adresse,
    email,
    tel,
    id_competence,
    id_softskill,
    id_metier,
    id_lieu,
    id_contrat,
    id_type_entreprise,
    id_seniorite,
    id_teletravail,
    id_domaine,
    salaire_min
  )
  select
    id_candidat,
    nom,
    prenom,
    adresse,
    email,
    tel,
    C.value as id_competence,
    S.value as id_softskill,
    M.value as id_metier,
    L.value as id_lieu,
    CO.value as id_contrat,
    T.value as id_type_entreprise,
    SE.value as id_seniorite,
    TE.value as id_teletravail,
    D.value as id_domaine,
    salaire_min 
  from {{ source('RAW','RAW_CANDIDAT') }},
    TABLE(FLATTEN(INPUT => id_competence, OUTER => TRUE)) C,
    TABLE(FLATTEN(INPUT => id_softskill, OUTER => TRUE)) S,
    TABLE(FLATTEN(INPUT => id_metier, OUTER => TRUE)) M,
    TABLE(FLATTEN(INPUT => id_lieu, OUTER => TRUE)) L,
    TABLE(FLATTEN(INPUT => id_contrat, OUTER => TRUE)) CO,
    TABLE(FLATTEN(INPUT => id_type_entreprise, OUTER => TRUE)) T,
    TABLE(FLATTEN(INPUT => id_seniorite, OUTER => TRUE)) SE,
    TABLE(FLATTEN(INPUT => id_teletravail, OUTER => TRUE)) TE,
    TABLE(FLATTEN(INPUT => id_domaine, OUTER => TRUE)) D
{% endset %}


-- Exécute l'insertion
{% do run_query(transformation_query) %}

