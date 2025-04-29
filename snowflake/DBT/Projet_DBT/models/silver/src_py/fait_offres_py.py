# models/src/fait_offres_py.py

from snowflake.snowpark.functions import col

def model(dbt, session):
    # 1️⃣ Config du modèle incrémental
    dbt.config(
        materialized='incremental',
        unique_key='id_local',
        incremental_strategy='merge',
        merge_update_columns=['id_lieu', 'id_contrat']
    )

    # 2️⃣ Charger la source RAW
    raw = session.table('RAW.RAW_OFFRE')

    # 3️⃣ Récupérer directement les DataFrames des refs
    lieu_df    = dbt.ref('matched_lieu_py')
    contrat_df = dbt.ref('matched_contrat_py')

    # 4️⃣ Jointures et projection
    fact_df = (
        raw
        .join(lieu_df,    on='id_local', how='left')
        .join(contrat_df, on='id_local', how='left')
        .select(
            col('title'),
            col('description'),
            col('id_local'),
            col('id_lieu'),
            col('id_contrat')
        
        )
        .dropDuplicates(['id_local'])
    )

    return fact_df
