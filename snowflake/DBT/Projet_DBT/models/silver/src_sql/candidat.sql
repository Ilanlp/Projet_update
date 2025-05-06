{{ config(materialized='table',tags=['sql']) }}

with flatten_candidat as (
    select 
        -- D'abord supprimer tout ce qui n'est pas chiffre ou espace
        id_candidat,
        nom,
        prenom,
        adresse,
        email,
        tel,
        split(regexp_replace(id_competence, '[^0-9 ]', ' '), ' ') as id_competence,
        split(regexp_replace(id_softskill, '[^0-9 ]', ' '), ' ') as id_softskill,
        split(regexp_replace(id_metier, '[^0-9 ]', ' '), ' ') as id_metier,
        split(regexp_replace(id_lieu, '[^0-9 ]', ' '), ' ') as id_lieu,
        split(regexp_replace(id_contrat, '[^0-9 ]', ' '), ' ') as id_contrat,
        split(regexp_replace(id_type_entreprise, '[^0-9 ]', ' '), ' ') as id_type_entreprise,
        split(regexp_replace(id_seniorite, '[^0-9 ]', ' '), ' ') as id_seniorite,
        split(regexp_replace(id_teletravail, '[^0-9 ]', ' '), ' ') as id_teletravail,
        split(regexp_replace(id_domaine, '[^0-9 ]', ' '), ' ') as id_domaine,
        salaire_min

    from {{ source('RAW','RAW_CANDIDAT') }}
),

candidat_exploded as ( 
    select
        id_candidat,
        nom,
        prenom,
        adresse,
        email,
        tel,
        trim(C.value) as id_competence,
        trim(S.value) as id_softskill,
        trim(E.value) as id_metier,
        trim(V.value) as id_lieu,
        trim(CO.value) as id_contrat,
        trim(T.value) as id_type_entreprise,
        trim(N.value) as id_seniorite,
        trim(TE.value) as id_teletravail,
        trim(D.value) as id_domaine,
        salaire_min
    from flatten_candidat,
    lateral flatten(input => id_competence) C,
    lateral flatten(input => id_softskill) S,
    lateral flatten(input => id_metier) E,
    lateral flatten(input => id_lieu) V,
    lateral flatten(input => id_contrat) CO,
    lateral flatten(input => id_type_entreprise) T,
    lateral flatten(input => id_seniorite) N,
    lateral flatten(input => id_teletravail) TE,
    lateral flatten(input => id_domaine) D,
    where length(trim(C.value)) > 0 
    and length(trim(S.value)) > 0
    and length(trim(E.value)) > 0
    and length(trim(V.value)) > 0
    and length(trim(CO.value)) > 0 
    and length(trim(T.value)) > 0 
    and length(trim(N.value)) > 0 
    and length(trim(TE.value)) > 0 
    and length(trim(D.value)) > 0  
)


select * from candidat_exploded