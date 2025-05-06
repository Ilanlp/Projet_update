{{ config(materialized='table',tags=['sql']) }}

with
offre as (
    select
        id_local,
        skills,
        description,
    from {{ref('RAW_OFFRE')}}
),

competence as (
    select 
        id,
        skill
    from {{ref("DIM_COMPETENCE")}}
),

matching as (
    select
        o.id_local,
        o.skills,
        c.skill,
        c.id
    from offre o
    inner join competence c
        on (
            lower(o.description) LIKE '% ' || lower(c.skill) || ' %'
            or lower(o.skills) LIKE '% ' || lower(c.skill) || ' %'
        )
)

select * from matching