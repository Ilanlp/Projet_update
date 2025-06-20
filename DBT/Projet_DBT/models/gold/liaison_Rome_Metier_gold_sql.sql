{{
    config(
        materialized='table'
    )
}}

SELECT 
    id_rome,
    id_metier
FROM {{ ref('Liaison_Rome_Metier') }} 