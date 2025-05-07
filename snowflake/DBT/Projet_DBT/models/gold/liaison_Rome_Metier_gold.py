# models/src/fait_offres_py.py

from snowflake.snowpark.functions import col

def model(dbt, session):
    # 1️⃣ Config du modèle incrémental
    dbt.config(
        materialized='table',
    )

   
    # 3️⃣ Récupérer directement les DataFrames des refs
    Rome_Metier_df    = dbt.ref('Liaison_Rome_Metier')
    

    # 4️⃣ Jointures et projection
    Rome_Metier_df = (
        Rome_Metier_df
        .select(
            col('id_rome'),
            col('id_metier'),
            
        )
    )

    return Rome_Metier_df
