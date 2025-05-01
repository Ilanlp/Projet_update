from snowflake.snowpark.functions import (
    split, lower, when, lit, col, row_number, element_at,trim,translate
)
from snowflake.snowpark.window import Window

def model(dbt, session):
    raw = session.table("RAW.RAW_OFFRE")
    dim = session.table("SILVER.DIM_ENTREPRISE")

      # 0) Nettoyer les espaces en début/fin
    raw_clean = trim(raw["company_name"])   # ou ltrim(raw["company_name"])
    dim_clean = trim(dim["nom_entreprise"])


    # 1) Extraction du premier mot (élément 1 de l'array)
    raw_first = element_at(split(raw_clean, lit(" ")), 0)
    dim_first = element_at(split(dim_clean, lit(" ")), 0)

    # 2) Conditions de matching
    exact_match = lower(raw["company_name"]) == lower(dim["nom_entreprise"])
    first_word_match = lower(dim_first) == lower(raw_first)
    
    

    # Création de la condition de jointure
    join_cond = exact_match | first_word_match

    # Jointure avec les tables
    df = (
        raw.join(dim, join_cond, how="left")
           .select(
               raw["id"],
               raw["id_local"],
               raw["company_name"],
               raw_first,
               dim_first,
               dim["SIREN"],
               dim["nom_entreprise"].alias("nom_entreprise"),
               when(exact_match, lit(1)).otherwise(lit(0)).alias("is_exact"),
               when(first_word_match, lit(1)).otherwise(lit(0)).alias("is_first_word"),
               dim["Categorie_entreprise"]
           )
    )

    # 3) Priorité catégorie entreprise
    priority = when(df["Categorie_entreprise"] == "GE",  lit(1)) \
               .when(df["Categorie_entreprise"] == "ETI", lit(2)) \
               .when(df["Categorie_entreprise"] == "PME", lit(3)) \
               .otherwise(lit(4)) \
               .alias("priority") 

    df = df.with_column("priority", priority)

    # 4) Fenêtre de ranking : exact > premier mot > partiel > catégorie
    w = Window.partition_by("id_local").order_by(
        col("is_exact").desc(),
        col("is_first_word").desc(),
        col("priority").asc()
    )

    best = (
        df.with_column("rn", row_number().over(w))
          .filter(col("rn") == 1)
          .drop("rn", "priority", "is_exact", "is_first_word")
    )

    return best
