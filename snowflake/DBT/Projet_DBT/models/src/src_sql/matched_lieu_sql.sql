{{
  config(
    materialized='table'
  )
}}

-- CTE pour les sources
with raw as (
    select
        id,
        id_local,
        location_name,
        latitude,
        longitude
    from {{ source('raw', 'analyses') }}
),

-- Table des lieux
dim_lieu as (
    select
        id_lieu,
        ville,
        departement,
        region,
        pays,
        latitude as lat2,
        longitude as lon2,
        population,
        code_postal
    from {{ source('dim_tables', 'dim_lieu') }}
),

-- Calcul des différents critères de matching
matching_prep as (
    select
        r.id,
        r.id_local,
        r.location_name,
        r.latitude  as lat1,
        r.longitude as lon1,
        d.id_lieu,
        d.ville      as dim_ville,

        -- Distance Haversine (en km)
        6371 * (2 * asin(
            sqrt(
                pow(sin((radians(r.latitude) - radians(d.lat2)) / 2), 2)
              + cos(radians(d.lat2)) * cos(radians(r.latitude))
                * pow(sin((radians(r.longitude) - radians(d.lon2)) / 2), 2)
            )
        )) as distance_km,

        -- Matching géographique
        case when 6371 * (2 * asin(
            sqrt(
                pow(sin((radians(r.latitude) - radians(d.lat2)) / 2), 2)
              + cos(radians(d.lat2)) * cos(radians(r.latitude))
                * pow(sin((radians(r.longitude) - radians(d.lon2)) / 2), 2)
            )
        )) < 10 then 1 else 0 end as is_coord,

        -- Matching textuel
        case when lower(r.location_name) like concat('%', lower(d.pays), '%') then 1 else 0 end as is_france,
        case when lower(r.location_name) like concat('%', lower(d.departement), '%') then 1 else 0 end as is_dept,
        case when lower(r.location_name) like concat('%', lower(d.ville), '%') then 1 else 0 end as is_name,
        case when lower(r.location_name) like concat('%', lower(d.region), '%') then 1 else 0 end as is_region,

        -- Extraction code département (2 chiffres)
        regexp_substr(
          cast(r.location_name as string),
          '\\s*([0-9]{2})\\s*',
          1,
          1,
          'e',
          1
        ) as dept_code,

        -- Matching code département
        case when regexp_substr(
                cast(r.location_name as string),
                '\\s*([0-9]{2})\\s*', 1, 1, 'e', 1
             ) is not null
             and substr(d.code_postal, 1, 2) = regexp_substr(
                cast(r.location_name as string),
                '\\s*([0-9]{2})\\s*', 1, 1, 'e', 1
             )
        then 1 else 0 end as is_dept_code,

        d.population
    from raw r
    left join dim_lieu d
      on true  -- on laisse le filtrage à la fenêtre
),

-- Application de la fenêtre pour ne garder que la meilleure correspondance
best_match as (
    select
        id,
        id_local,
        location_name,
        lat1  as latitude,
        lon1  as longitude,
        id_lieu,
        dim_ville
    from (
        select
            m.*,
            row_number() over (
                partition by id_local
                order by
                  is_coord desc,
                  distance_km asc,
                  is_france desc,
                  is_dept_code desc,
                  is_name desc,
                  is_dept desc,
                  is_region desc,
                  population desc
            ) as rn
        from matching_prep m
    ) t
    where rn = 1
)

-- Résultat final
select *
from best_match
