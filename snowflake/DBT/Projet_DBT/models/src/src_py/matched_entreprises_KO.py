from snowflake.snowpark.functions import lower, lit

def model(dbt, session):
    raw   = session.table("RAW.ANALYSES")
    dim_e = session.table("PUBLIC.DIM_ENTREPRISE")

    matched = (
        raw
        .join(
            dim_e,
            lower(raw["company_name"]).contains(lower(dim_e["nom"])),
            how="inner"
        )
        .select(
            raw["id"].alias("id"),
            dim_e["id_entreprise"].alias("id_entreprise")
        )
    )
    return matched
