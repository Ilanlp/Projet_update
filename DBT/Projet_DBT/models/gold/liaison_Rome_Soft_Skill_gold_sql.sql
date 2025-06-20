{{
    config(
        materialized='table'
    )
}}

SELECT 
    id_rome,
    id_softskill
FROM {{ ref('Liaison_Rome_Soft_Skill') }} 