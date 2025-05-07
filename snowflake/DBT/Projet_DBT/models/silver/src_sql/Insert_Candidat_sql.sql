{{ config(
    materialized='ephemeral',
    tags=['sql']
) }}

-- Ce modèle traite les données mais ne crée pas de table DBT
-- Au lieu de cela, il prépare les données pour insertion

WITH flatten_candidat AS (
    SELECT
        id_candidat,
        nom,
        prenom,
        adresse,
        email,
        tel,
        split(regexp_replace(id_competence, '[^0-9 ]', ' '), ' ') AS id_competence,
        split(regexp_replace(id_softskill, '[^0-9 ]', ' '), ' ') AS id_softskill,
        split(regexp_replace(id_metier, '[^0-9 ]', ' '), ' ') AS id_metier,
        split(regexp_replace(id_lieu, '[^0-9 ]', ' '), ' ') AS id_lieu,
        split(regexp_replace(id_contrat, '[^0-9 ]', ' '), ' ') AS id_contrat,
        split(regexp_replace(id_type_entreprise, '[^0-9 ]', ' '), ' ') AS id_type_entreprise,
        split(regexp_replace(id_seniorite, '[^0-9 ]', ' '), ' ') AS id_seniorite,
        split(regexp_replace(id_teletravail, '[^0-9 ]', ' '), ' ') AS id_teletravail,
        split(regexp_replace(id_domaine, '[^0-9 ]', ' '), ' ') AS id_domaine,
        salaire_min
    FROM {{ source('RAW', 'RAW_CANDIDAT') }}
),
candidat_exploded AS (
    SELECT
        id_candidat,
        nom,
        prenom,
        adresse,
        email,
        tel,
        trim(C.value) AS id_competence,
        trim(S.value) AS id_softskill,
        trim(E.value) AS id_metier,
        trim(V.value) AS id_lieu,
        trim(CO.value) AS id_contrat,
        trim(T.value) AS id_type_entreprise,
        trim(N.value) AS id_seniorite,
        trim(TE.value) AS id_teletravail,
        trim(D.value) AS id_domaine,
        salaire_min
    FROM flatten_candidat,
        LATERAL flatten(input => id_competence) C,
        LATERAL flatten(input => id_softskill) S,
        LATERAL flatten(input => id_metier) E,
        LATERAL flatten(input => id_lieu) V,
        LATERAL flatten(input => id_contrat) CO,
        LATERAL flatten(input => id_type_entreprise) T,
        LATERAL flatten(input => id_seniorite) N,
        LATERAL flatten(input => id_teletravail) TE,
        LATERAL flatten(input => id_domaine) D
    WHERE length(trim(C.value)) > 0
        AND length(trim(S.value)) > 0
        AND length(trim(E.value)) > 0
        AND length(trim(V.value)) > 0
        AND length(trim(CO.value)) > 0
        AND length(trim(T.value)) > 0
        AND length(trim(N.value)) > 0
        AND length(trim(TE.value)) > 0
        AND length(trim(D.value)) > 0
)


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
SELECT
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
FROM candidat_exploded

