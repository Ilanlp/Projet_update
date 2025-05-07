# models/src/fait_offres_py.py

from snowflake.snowpark.functions import col

def model(dbt, session):
    # 1️⃣ Config du modèle incrémental
    dbt.config(
        materialized='table',
    )

    # 2️⃣ Charger la source RAW
    raw = session.table('RAW.RAW_OFFRE').alias("raw")

    # 3️⃣ Récupérer directement les DataFrames des refs
    lieu_df    = dbt.ref('Match_Lieu_py')
    contrat_df = dbt.ref('Match_Contrat_py')
    date_df    = dbt.ref('Match_Date_py')
    entreprise_df = dbt.ref('Match_Entreprise_py')
    seniorite_df = dbt.ref('Match_Seniorite_py')
    teletravail_df = dbt.ref('Match_Teletravail_py')
    domaine_df = dbt.ref('Match_Domaine_sql')
    date_df=dbt.ref('Match_Date_py')

    # 4️⃣ Jointures et projection
    fact_df = (
        raw
        .join(lieu_df,    on='id_local', how='left')
        .join(contrat_df, on='id_local', how='left')
        .join(date_df, on='id_local', how='left')
        .join(entreprise_df, on='id_local', how='left')
        .join(seniorite_df, on='id_local', how='left')
        .join(teletravail_df, on='id_local', how='left')
        .join(domaine_df, on='id_local', how='left')
        
        .select(
            col('title'),
            col("description"),
            col('id_local'),
            col('id_lieu'),
            col('id_contrat'),
            col('id_date_created'),
            col('id_date_updated'),
            col('id_entreprise'),
            col('id_seniorite'),
            col('id_teletravail'),
            col('id_domaine'),
            
        )
    )

    return fact_df
