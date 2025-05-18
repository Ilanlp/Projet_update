{{ config(
    materialized='table',
    tags=['sql'],
    post_hook=[
        "USE SCHEMA SILVER",
        "CREATE STAGE IF NOT EXISTS candidat",
        "COPY INTO @candidat/text_candidat_data.csv.gz FROM text_candidat_sql FILE_FORMAT = (TYPE = 'CSV' FIELD_DELIMITER = ';') HEADER=TRUE OVERWRITE = TRUE SINGLE=TRUE"
    ]
) }}

with candidat as (select * from {{source('dim_tables','DIM_CANDIDAT')}}),
competence as (select * from {{source('dim_tables','DIM_COMPETENCE')}}),
softskill as (select * from {{source('dim_tables','DIM_SOFTSKILL')}}),
metier as (select * from {{source('dim_tables','DIM_METIER')}}),
lieu as (select * from {{source('dim_tables','DIM_LIEU')}}),
contrat as (select * from {{source('dim_tables','DIM_CONTRAT')}}),
type_entreprise as (select * from {{source('dim_tables','DIM_TYPE_ENTREPRISE')}}), 
seniorite as (select * from {{source('dim_tables','DIM_SENIORITE')}}),
teletravail as (select * from {{source('dim_tables','DIM_TELETRAVAIL')}}),
domaine as (select * from {{source('dim_tables','DIM_DOMAINE')}}),

competence_text as (
    select 
        id_candidat,
        nom,
        ARRAY_TO_STRING(ARRAY_AGG(description),' ') as c_description
    from (    
        select 
            distinct(id_candidat),
            candidat.nom,
            c.skill ||' '|| c.type as description
        from candidat
        left join competence as c on candidat.id_competence = c.id_competence 
    )
    group by id_candidat, nom
),

softskill_text as (
    select
        id_candidat,
        nom,
        ARRAY_TO_STRING(ARRAY_AGG(description),' ') as s_description
    from(
        select
            distinct(id_candidat),
            candidat.nom,
            s.summary ||' '|| s.details as description
        from candidat
        left join softskill as s on candidat.id_softskill = s.id_softskill
    ) 
    group by id_candidat, nom
),

metier_text as (
    select
        id_candidat,
        nom,
        ARRAY_TO_STRING(ARRAY_AGG(description),' ') as m_description
    from(
        select
            distinct(id_candidat),
            candidat.nom,
            m.id_appellation ||' '|| m.nom as description
        from candidat
        left join metier as m on candidat.id_metier = m.id_metier
    ) 
    group by id_candidat, nom
),

lieu_text as (
    select
        id_candidat,
        nom,
        ARRAY_TO_STRING(ARRAY_AGG(description),' ') as l_description
    from(
        select
            distinct(id_candidat),
            candidat.nom,
            l.code_postal ||' '|| l.departement ||' '|| l.latitude ||' '|| l.longitude ||' '|| l.pays ||' '|| l.population ||' '|| l.region ||' '|| l.ville as description
        from candidat
        left join lieu as l on candidat.id_lieu = l.id_lieu
    ) 
    group by id_candidat, nom
),

contrat_text as (
    select
        id_candidat,
        nom,
        ARRAY_TO_STRING(ARRAY_AGG(description),' ') as co_description
    from(
        select
            distinct(id_candidat),
            candidat.nom,
            co.type_contrat as description
        from candidat
        left join contrat as co on candidat.id_contrat = co.id_contrat
    ) 
    group by id_candidat, nom
),


type_entreprise_text as (
    select
        id_candidat,
        nom,
        ARRAY_TO_STRING(ARRAY_AGG(description),' ') as t_description
    from(
        select
            distinct(id_candidat),
            candidat.nom,
            t.type_entreprise ||' '|| t.taille_min_salaries ||' '|| t.taille_max_salaries ||' '|| t.categorie_taille as description
        from candidat
        left join type_entreprise as t on candidat.id_type_entreprise = t.id_type_entreprise
    ) 
    group by id_candidat, nom
),

seniorite_text as (
    select 
        id_candidat,
        nom,
        ARRAY_TO_STRING(ARRAY_AGG(description),' ') as se_description
    from (    
        select 
            distinct(id_candidat),
            candidat.nom,
            se.type_seniorite as description
        from candidat
        left join seniorite as se on candidat.id_seniorite = se.id_seniorite 
    )
    group by id_candidat, nom
),

teletravail_text as (
    select 
        id_candidat,
        nom,
        ARRAY_TO_STRING(ARRAY_AGG(description),' ') as te_description
    from (    
        select 
            distinct(id_candidat),
            candidat.nom,
            te.type_teletravail as description
        from candidat
        left join teletravail as te on candidat.id_teletravail = te.id_teletravail 
    )
    group by id_candidat, nom
),

domaine_text as (
    select 
        id_candidat,
        nom,
        ARRAY_TO_STRING(ARRAY_AGG(description),' ') as d_description
    from (    
        select 
            distinct(id_candidat),
            candidat.nom,
            d.nom_domaine ||' '|| d.code_domaine as description
        from candidat
        left join domaine as d on candidat.id_domaine = d.id_domaine
    )
    group by id_candidat, nom
),

text as (
    select 
        c.id_candidat,
        c.nom,
        c_description ||' '|| 
        s_description ||' '||
        m_description ||' '||
        l_description ||' '||
        co_description ||' '||
        t_description ||' '||
        se_description ||' '||
        te_description ||' '||
        d_description
        as text
    from competence_text as c 
    left join softskill_text as s on c.id_candidat = s.id_candidat
    left join metier_text as m on c.id_candidat = m.id_candidat
    left join lieu_text as l on c.id_candidat = l.id_candidat
    left join contrat_text as co on c.id_candidat = co.id_candidat
    left join type_entreprise_text as t on c.id_candidat = t.id_candidat
    left join seniorite_text as se on c.id_candidat = se.id_candidat
    left join teletravail_text as te on c.id_candidat = te.id_candidat
    left join domaine_text as d on c.id_candidat = d.id_candidat
)

select * from text

