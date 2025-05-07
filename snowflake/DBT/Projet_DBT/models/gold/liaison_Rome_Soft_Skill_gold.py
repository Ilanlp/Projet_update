# models/src/fait_offres_py.py

from snowflake.snowpark.functions import col

def model(dbt, session):
    # 1️⃣ Config du modèle incrémental
    dbt.config(
        materialized='table',
    )

   
    # 3️⃣ Récupérer directement les DataFrames des refs
    Rome_Soft_Skill_df    = dbt.ref('Liaison_Rome_Soft_Skill')
    

    # 4️⃣ Jointures et projection
    Rome_Soft_Skill_df = (
        Rome_Soft_Skill_df
        .select(
            col('id_rome'),
            col('id_softskill'),
            
        )
    )

    return Rome_Soft_Skill_df
