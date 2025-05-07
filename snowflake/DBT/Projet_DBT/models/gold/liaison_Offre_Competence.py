# models/src/fait_offres_py.py

from snowflake.snowpark.functions import col

def model(dbt, session):
    # 1️⃣ Config du modèle incrémental
    dbt.config(
        materialized='table',
    )

   
    # 3️⃣ Récupérer directement les DataFrames des refs
    competence_df    = dbt.ref('Match_Competence_sql')
    

    # 4️⃣ Jointures et projection
    Liaison_Competence_df = (
        competence_df
        .select(
            col('id_local'),
            col('id_competence'),
            
        )
    )

    return Liaison_Competence_df
