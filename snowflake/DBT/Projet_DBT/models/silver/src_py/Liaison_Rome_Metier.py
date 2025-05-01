from snowflake.snowpark.functions import lower

def model(dbt, session):
    # Chargement des tables
    raw        = session.table("RAW.RAW_ROME_METIER").alias("r")
    dim_rome   = session.table("SILVER.DIM_ROMECODE").alias("d_rome")
    dim_metier = session.table("SILVER.DIM_METIER").alias("d_metier")

    # Jointure sur code ROME
    raw_with_rome = raw.join(
        dim_rome,
        lower(raw["CODE_ROME"]) == lower(dim_rome["CODE_ROME"]),
        how="inner"
    )

    # Jointure sur appellation métier
    joined = raw_with_rome.join(
        dim_metier,
        lower(raw["CODE_APPELLATION"]) == lower(dim_metier["ID_APPELLATION"]),
        how="inner"
    )

    # Sélection uniquement des IDs
    result = joined.select(
        dim_rome["ID_ROME"].alias("id_rome"),
        dim_metier["ID_METIER"].alias("id_metier")
    ).distinct()

    return result
