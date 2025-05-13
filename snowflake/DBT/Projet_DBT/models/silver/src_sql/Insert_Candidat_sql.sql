{{ config(materialized='ephemeral',tags=['sql1']) }}

{% set delete_query %}
  DELETE FROM {{ source('dim_tables', 'DIM_CANDIDAT') }}
{% endset %}

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

{% set copy_to_stage %}
    USE SCHEMA SILVER;
    CREATE STAGE IF NOT EXISTS candidat;
    COPY INTO @candidat/candidat_data.csv.gz FROM {{ source('dim_tables', 'DIM_CANDIDAT') }}
    FILE_FORMAT = (TYPE = 'CSV' FIELD_DELIMITER = ',' COMPRESSION = GZIP) 
    HEADER = TRUE 
    OVERWRITE = TRUE 
    SINGLE = TRUE
    MAX_FILE_SIZE = 5000000000;
{% endset %}

-- Exécute la suppression des données existantes
{% do run_query(delete_query) %}

-- Exécute l'insertion
{% do run_query(transformation_query) %}

-- Copy de la table dans le stage
{% do run_query(copy_to_stage) %}