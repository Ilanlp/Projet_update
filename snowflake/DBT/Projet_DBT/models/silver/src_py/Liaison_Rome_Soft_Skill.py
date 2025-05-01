from snowflake.snowpark.functions import lower

def model(dbt, session):
    # Chargement des tables
    raw_ss        = session.table("RAW.RAW_SOFTSKILL").alias("rss")
    dim_rome   = session.table("SILVER.DIM_ROMECODE").alias("d_rome")
    dim_ss = session.table("SILVER.DIM_SOFTSKILL").alias("dss")

    # Jointure sur code ROME
    raw_with_rome = raw_ss.join(
        dim_rome,
        lower(raw_ss["CODE_ROME"]) == lower(dim_rome["CODE_ROME"]),
        how="inner"
    )

    # Jointure sur appellation métier
    joined = raw_with_rome.join(
        dim_ss,
        lower(raw_ss["SUMMARY"]) == lower(dim_ss["SUMMARY"]),
        how="inner"
    )

    # Sélection uniquement des IDs
    result = joined.select(
        dim_rome["ID_ROME"].alias("id_rome"),
        dim_ss["ID_SOFTSKILL"].alias("id_softskill")
    ).distinct()

    return result