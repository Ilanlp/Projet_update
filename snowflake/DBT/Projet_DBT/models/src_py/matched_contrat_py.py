# models/src/matched_contrat.py

from snowflake.snowpark.functions import (
    col, lower, lit, when, row_number
)
from snowflake.snowpark.window import Window

def model(dbt, session):
    raw         = session.table("RAW.ANALYSES")
    dim_contrat = session.table("PUBLIC.Dim_Contrat")

    # 1) Conditions de matching
    exact_match_raw   = lower(raw["contract_type"]) == lower(dim_contrat["type_contrat"])
    partial_match_raw = lower(raw["description"]).contains(lower(dim_contrat["type_contrat"]))

    # 2) LEFT JOIN pour conserver TOUT raw même sans contrat
    df = (
        raw
        .join(
            dim_contrat,
            exact_match_raw | partial_match_raw,
            how="left"
        )
        .select(
            raw["id"].alias("id"),
            raw["ID_LOCAL"].alias("id_local"),
            dim_contrat["id_contrat"].alias("id_contrat"),
            # flags castés en 1/0, NULL => 0
            when(exact_match_raw, lit(1)).otherwise(lit(0)).alias("is_exact"),
            when(partial_match_raw, lit(1)).otherwise(lit(0)).alias("is_partial")
        )
    )

    # 3) Fenêtre pour ne garder qu'un seul id_contrat par id
    w = Window.partition_by("id").order_by(
        col("is_exact").desc(),    # 1) correspondance exacte
        col("is_partial").desc()   # 2) correspondance partielle
    )

    best = (
        df
        .with_column("rn", row_number().over(w))
        .filter(col("rn") == 1)
        .drop("is_exact", "is_partial", "rn")
    )

    return best
