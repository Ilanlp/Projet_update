{{ config(materialized='table',tags=['sql']) }}

with
offre as (
    select
        id_local,
        skills,
        description,
    from {{source('RAW','RAW_OFFRE')}}
),

competence as (
    select 
        id_competence,
        skill
    from {{source("dim_tables","DIM_COMPETENCE")}}
),

matching as (
    select
        o.id_local,
        o.skills,
        c.skill,
        c.id_competence
    from offre o
    inner join competence c
        on (
            lower(o.description) LIKE '% ' || lower(c.skill) || ' %'
            or lower(o.skills) LIKE '% ' || lower(c.skill) || ' %'
        )
)

select * from matching