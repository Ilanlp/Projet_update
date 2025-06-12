{{ 
  config(
    materialized = 'incremental',
    unique_key   = 'id_local',
    on_schema_change = 'append_new_columns'
  ) 
}}

WITH base AS (

    SELECT
        
        -- Faits
        fo.id_offre,
        fo.id_local,
        roc.title,
        roc.description,

        -- Contrat
        dc.type_contrat,

        -- Domaine
        dd.code_domaine,
        dd.nom_domaine,

        -- Lieu
        dl.code_postal,
        dl.ville,
        dl.departement,
        dl.region,
        dl.pays,
        dl.latitude,
        dl.longitude,
        dl.population,

        -- Dates
        d1.mois AS mois_creation,
        d1.jour AS jour_creation,
        d1.mois_nom AS mois_nom_creation,
        d1.jour_semaine AS jour_semaine_creation,
        d1.week_end AS week_end_creation,

        d2.mois AS mois_modification,
        d2.jour AS jour_modification,
        d2.mois_nom AS mois_nom_modification,
        d2.jour_semaine AS jour_semaine_modification,
        d2.week_end AS week_end_modification,

        -- Télétravail
        dt.type_teletravail,

        -- Seniorité
        ds.type_seniorite,

        -- Rome
        dr.code_rome,

        -- Entreprise
        de.nom_entreprise,
        de.categorie_entreprise,
        de.date_creation_entreprise,

        -- Compétences
        comp.skill,
        comp.type,

        -- Softskills
        ss.summary,
        ss.details,

        -- Métiers
        dm.nom AS nom_metier

    FROM {{ source('gold_tables', 'FAIT_OFFRE') }} fo
    LEFT JOIN {{ source('RAW', 'RAW_OFFRE_CLEAN') }} roc ON fo.id_local = roc.id_local
    LEFT JOIN {{ source('dim_tables', 'DIM_CONTRAT') }} dc ON fo.id_contrat = dc.id_contrat
    LEFT JOIN {{ source('dim_tables', 'DIM_DOMAINE') }} dd ON fo.id_domaine = dd.id_domaine
    LEFT JOIN {{ source('dim_tables', 'DIM_LIEU') }} dl ON fo.id_lieu = dl.id_lieu
    LEFT JOIN {{ source('dim_tables', 'DIM_DATE') }} d1 ON fo.id_date_creation = d1.id_date
    LEFT JOIN {{ source('dim_tables', 'DIM_DATE') }} d2 ON fo.id_date_modification = d2.id_date
    LEFT JOIN {{ source('dim_tables', 'DIM_TELETRAVAIL') }} dt ON fo.id_teletravail = dt.id_teletravail
    LEFT JOIN {{ source('dim_tables', 'DIM_SENIORITE') }} ds ON fo.id_seniorite = ds.id_seniorite
    LEFT JOIN {{ source('dim_tables', 'DIM_ROMECODE') }} dr ON fo.id_rome = dr.id_rome
    LEFT JOIN {{ source('dim_tables', 'DIM_ENTREPRISE') }} de ON fo.id_entreprise = de.siren
    LEFT JOIN {{ source('gold_tables', 'LIAISON_ROME_METIER_GOLD_SQL') }} lrm ON fo.id_rome = lrm.id_rome
    LEFT JOIN {{ source('dim_tables', 'DIM_METIER') }} dm ON lrm.id_metier = dm.id_metier
    LEFT JOIN {{ source('gold_tables', 'LIAISON_OFFRE_COMPETENCE') }} loc ON fo.id_offre = loc.id_offre
    LEFT JOIN {{ source('dim_tables', 'DIM_COMPETENCE') }} comp ON loc.id_competence = comp.id_competence
    LEFT JOIN {{ source('gold_tables', 'LIAISON_ROME_SOFT_SKILL_GOLD_SQL') }} lrs ON fo.id_rome = lrs.id_rome
    LEFT JOIN {{ source('dim_tables', 'DIM_SOFTSKILL') }} ss ON lrs.id_softskill = ss.id_softskill

)

SELECT
    id_offre as id,
    id_local,
    title,
    description,
    type_contrat,
    code_domaine,
    nom_domaine,
    code_postal,
    ville,
    departement,
    region,
    pays,
    latitude,
    longitude,
    population,
    mois_creation,
    jour_creation,
    mois_nom_creation,
    jour_semaine_creation,
    week_end_creation,
    mois_modification,
    jour_modification,
    mois_nom_modification,
    jour_semaine_modification,
    week_end_modification,
    type_teletravail,
    type_seniorite,
    code_rome,
    nom_entreprise,
    categorie_entreprise,
    date_creation_entreprise,
    LISTAGG(DISTINCT skill, ', ') WITHIN GROUP (ORDER BY skill) AS competences,
    LISTAGG(DISTINCT type, ', ') WITHIN GROUP (ORDER BY type) AS types_competences,
    LISTAGG(DISTINCT summary, ', ') WITHIN GROUP (ORDER BY summary) AS softskills_summary,
    LISTAGG(DISTINCT details, ' | ') WITHIN GROUP (ORDER BY details) AS softskills_details,
    LISTAGG(DISTINCT nom_metier, ', ') WITHIN GROUP (ORDER BY nom_metier) AS nom_metier

FROM base
GROUP BY
    id_offre,
    id_local,
    title,
    description,
    type_contrat,
    code_domaine,
    nom_domaine,
    code_postal,
    ville,
    departement,
    region,
    pays,
    latitude,
    longitude,
    population,
    mois_creation,
    jour_creation,
    mois_nom_creation,
    jour_semaine_creation,
    week_end_creation,
    mois_modification,
    jour_modification,
    mois_nom_modification,
    jour_semaine_modification,
    week_end_modification,
    type_teletravail,
    type_seniorite,
    code_rome,
    nom_entreprise,
    categorie_entreprise,
    date_creation_entreprise
