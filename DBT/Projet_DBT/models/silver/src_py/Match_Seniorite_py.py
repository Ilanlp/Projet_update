from snowflake.snowpark.functions import (
    col, lower, lit, when, row_number
)
from snowflake.snowpark.window import Window
import datetime

def model(dbt, session):
    today = datetime.date.today()
    raw = session.table("RAW.RAW_OFFRE_CLEAN").filter(
        col("DATE_EXTRACTION").cast("date") == today
    )
    dim_seniorite = session.table("SILVER.DIM_SENIORITE")

    # 1) Matchings exact & partiel
    exact_match_raw = lower(raw["experience_required"]) \
                     .contains(lower(dim_seniorite["type_seniorite"]))
    partial_match_raw = lower(raw["description"]) \
                       .contains(lower(dim_seniorite["type_seniorite"]))

    # 2) Matching permissif par mots-clés avec contains()

    # Junior
    is_junior = (
        lower(dim_seniorite["type_seniorite"]) == lit("junior")
    ) & (
        lower(raw["description"]).contains(lower(lit("junior")))
        | lower(raw["description"]).contains(lower(lit("débutant")))
        | lower(raw["description"]).contains(lower(lit("debutant")))
        | lower(raw["description"]).contains(lower(lit("première expérience")))
        | lower(raw["description"]).contains(lower(lit("premiere experience")))
        | lower(raw["description"]).contains(lower(lit("premier emploi")))
        | lower(raw["experience_required"]).contains(lower(lit("débutant accepté")))
        | lower(raw["experience_required"]).contains(lower(lit("debutant accepte")))
        | lower(raw["experience_required"]).contains(lower(lit("expérience exigée")))
        | lower(raw["experience_required"]).contains(lower(lit("experience exigee")))
    )

    # Confirmé
    is_confirme = (
        lower(dim_seniorite["type_seniorite"]) == lit("confirmé")
    ) & (
        lower(raw["description"]).contains(lower(lit("confirmé")))
        | lower(raw["description"]).contains(lower(lit("confirme")))
        | lower(raw["description"]).contains(lower(lit("expérimenté")))
        | lower(raw["description"]).contains(lower(lit("experimente")))
        | lower(raw["description"]).contains(lower(lit("2 à 5 ans")))
        | lower(raw["description"]).contains(lower(lit("2 a 5 ans")))
        | lower(raw["description"]).contains(lower(lit("2-5 ans")))
        | lower(raw["experience_required"]).contains(lower(lit("expérience souhaitée")))
        | lower(raw["experience_required"]).contains(lower(lit("experience souhaitee")))
    )

    # Senior
    is_senior = (
        lower(dim_seniorite["type_seniorite"]) == lit("senior")
    ) & (
        lower(raw["description"]).contains(lower(lit("senior")))
        | lower(raw["description"]).contains(lower(lit("expert")))
        | lower(raw["description"]).contains(lower(lit("5 ans minimum")))
        | lower(raw["description"]).contains(lower(lit("5 ans d'expérience")))
        | lower(raw["description"]).contains(lower(lit("5 ans d'experience")))
        | lower(raw["description"]).contains(lower(lit("plus de 5 ans")))
        | lower(raw["experience_required"]).contains(lower(lit("expérience exigée")))
        | lower(raw["experience_required"]).contains(lower(lit("experience exigee")))
    )

    # 3) Condition de jointure
    join_cond = (
        exact_match_raw | partial_match_raw
        | is_junior | is_confirme | is_senior
    )

    # 4) Join et flags
    df = (
        raw.join(dim_seniorite, join_cond, how="left")
           .select(
               raw["id_offre"].alias("id_offre"),
               raw["ID_LOCAL"].alias("id_local"),
               dim_seniorite["id_seniorite"].alias("id_seniorite"),
               raw["EXPERIENCE_REQUIRED"].alias("experience_required"),
               when(exact_match_raw,   lit(1)).otherwise(lit(0)).alias("is_exact"),
               when(partial_match_raw, lit(1)).otherwise(lit(0)).alias("is_partial"),
               when(is_junior,         lit(1)).otherwise(lit(0)).alias("is_junior_regex"),
               when(is_confirme,       lit(1)).otherwise(lit(0)).alias("is_confirme_regex"),
               when(is_senior,         lit(1)).otherwise(lit(0)).alias("is_senior_regex")
           )
    )

    # 5) Fenêtre de priorisation
    w = Window.partition_by("id_local").order_by(
        col("is_exact")        .desc(),
        col("is_partial")      .desc(),
        col("is_senior_regex") .desc(),
        col("is_confirme_regex").desc(),
        col("is_junior_regex") .desc()
    )

    best = (
        df.with_column("rn", row_number().over(w))
          .filter(col("rn") == 1)
          .drop("is_exact", "is_partial",
                "is_junior_regex", "is_confirme_regex",
                "is_senior_regex", "rn")
    )

    return best 