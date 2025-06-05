CREATE OR REPLACE TABLE ONE_BIG_TABLE AS
SELECT -- ID auto-incrémental
    ROW_NUMBER() OVER (
        ORDER BY fo.id_local
    ) AS id,
    -- Faits
    fo.id_local,
    fo.title,
    fo.description,
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
    --Entreprise 
    de.nom_entreprise,
    de.categorie_entreprise,
    de.date_creation_entreprise,
    -- Compétences concaténées
    LISTAGG(DISTINCT comp.skill, ', ') WITHIN GROUP (
        ORDER BY comp.skill
    ) AS competences,
    LISTAGG(DISTINCT comp.type, ', ') WITHIN GROUP (
        ORDER BY comp.type
    ) AS types_competences,
    -- Softskills concaténés
    LISTAGG(DISTINCT ss.summary, ', ') WITHIN GROUP (
        ORDER BY ss.summary
    ) AS softskills_summary,
    LISTAGG(DISTINCT ss.details, ' | ') WITHIN GROUP (
        ORDER BY ss.details
    ) AS softskills_details,
    -- Métiers concaténés
    LISTAGG(DISTINCT dm.nom, ', ') WITHIN GROUP (
        ORDER BY dm.nom
    ) AS nom_metier
FROM FAIT_OFFRE fo
    LEFT JOIN DIM_CONTRAT dc ON fo.id_contrat = dc.id_contrat
    LEFT JOIN DIM_DOMAINE dd ON fo.id_domaine = dd.id_domaine
    LEFT JOIN DIM_LIEU dl ON fo.id_lieu = dl.id_lieu
    LEFT JOIN DIM_DATE d1 ON fo.id_date_creation = d1.id_date
    LEFT JOIN DIM_DATE d2 ON fo.id_date_modification = d2.id_date
    LEFT JOIN DIM_TELETRAVAIL dt ON fo.id_teletravail = dt.id_teletravail
    LEFT JOIN DIM_SENIORITE ds ON fo.id_seniorite = ds.id_seniorite
    LEFT JOIN DIM_ROMECODE dr ON fo.id_rome = dr.id_rome
    LEFT JOIN DIM_ENTREPRISE de ON fo.id_entreprise = de.siren
    LEFT JOIN LIAISON_ROME_METIER_GOLD_SQL lrm ON fo.id_rome = lrm.id_rome
    LEFT JOIN DIM_METIER dm ON lrm.id_metier = dm.id_metier
    LEFT JOIN LIAISON_OFFRE_COMPETENCE loc ON fo.id_local = loc.id_local
    LEFT JOIN DIM_COMPETENCE comp ON loc.id_competence = comp.id_competence
    LEFT JOIN LIAISON_ROME_SOFT_SKILL_GOLD_SQL lrs ON fo.id_rome = lrs.id_rome
    LEFT JOIN DIM_SOFTSKILL ss ON lrs.id_softskill = ss.id_softskill
GROUP BY fo.id_local,
    fo.title,
    fo.description,
    dc.type_contrat,
    de.nom_entreprise,
    de.categorie_entreprise,
    de.date_creation_entreprise,
    dd.code_domaine,
    dd.nom_domaine,
    dl.code_postal,
    dl.ville,
    dl.departement,
    dl.region,
    dl.pays,
    dl.latitude,
    dl.longitude,
    dl.population,
    d1.mois,
    d1.jour,
    d1.mois_nom,
    d1.jour_semaine,
    d1.week_end,
    d2.mois,
    d2.jour,
    d2.mois_nom,
    d2.jour_semaine,
    d2.week_end,
    dt.type_teletravail,
    ds.type_seniorite,
    dr.code_rome;