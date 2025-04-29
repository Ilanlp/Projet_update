from snowflake.snowpark.functions import col, lower, lit, when, row_number
from snowflake.snowpark.window import Window

def model(dbt, session):
    raw = session.table("RAW.RAW_OFFRE")
    dim = session.table("SILVER.DIM_ENTREPRISE")

    # 1) Matching exact et partiel (insensible à la casse)
    exact_match = lower(raw["company_name"]) == lower(dim["nom_entreprise"])
    partial_match = lower(raw["company_name"]).contains(lower(dim["nom_entreprise"]))
    partial_match_bis = lower(dim["nom_entreprise"]).contains(lower(raw["company_name"]))

    join_cond = exact_match | partial_match | partial_match_bis

    df = (
        raw.join(dim, join_cond, how="left")
           .select(
               raw["id"],
               raw["id_local"],
               raw["company_name"],
               dim["SIREN"],
               dim["nom_entreprise"].alias("dim_nom_entreprise"),
               when(exact_match, lit(1)).otherwise(lit(0)).alias("is_exact"),
               when(partial_match, lit(1)).otherwise(lit(0)).alias("is_partial"),
               when(partial_match_bis, lit(1)).otherwise(lit(0)).alias("is_partial_bis"),
               dim["Categorie_entreprise"]
           )
    )

    # 2) Priorité catégorie entreprise
    priority = when(df["Categorie_entreprise"] == "GE",  lit(1)) \
               .when(df["Categorie_entreprise"] == "ETI", lit(2)) \
               .when(df["Categorie_entreprise"] == "PME", lit(3)) \
               .otherwise(lit(4)) \
               .alias("priority")

    df = df.with_column("priority", priority)

    # 3) Fenêtre de ranking : exact > partiel > catégorie
    w = Window.partition_by("id_local").order_by(
        col("priority").asc(),
        col("is_exact").desc(),
        col("is_partial_bis").desc(),
        col("is_partial").desc()
        
    )

    best = (
        df.with_column("rn", row_number().over(w))
          .filter(col("rn") == 1)
          .drop("rn", "priority", "is_exact", "is_partial")
    )

    return best
