from snowflake.snowpark.functions import (
    col, lower, lit, when, row_number
)
from snowflake.snowpark.window import Window
import datetime

def model(dbt, session):
    today = datetime.date.today()
    raw = session.table("RAW.RAW_OFFRE").filter(
        col("DATE_EXTRACTION").cast("date") == today
    )
    dim_teletravail = session.table("SILVER.DIM_TELETRAVAIL")

    # 1) Matchings exact & partiel
    exact_match_raw = lower(raw["description"]) \
                     .contains(lower(dim_teletravail["type_teletravail"]))
    partial_match_raw = lower(raw["description"]) \
                       .contains(lower(dim_teletravail["type_teletravail"]))

    # 2) Matching permissif par mots-clés avec contains()

    # À distance
    is_distance = (
        lower(dim_teletravail["type_teletravail"]) == lit("à distance")
    ) & (
        lower(raw["description"]).contains(lower(lit("télétravail")))
        | lower(raw["description"]).contains(lower(lit("teletravail")))
        | lower(raw["description"]).contains(lower(lit("remote")))
        | lower(raw["description"]).contains(lower(lit("à distance")))
        | lower(raw["description"]).contains(lower(lit("a distance")))
        | lower(raw["description"]).contains(lower(lit("100% remote")))
        | lower(raw["description"]).contains(lower(lit("full remote")))
        | lower(raw["description"]).contains(lower(lit("travail à distance")))
        | lower(raw["description"]).contains(lower(lit("travail a distance")))
        | lower(raw["description"]).contains(lower(lit("travail depuis chez vous")))
        | lower(raw["description"]).contains(lower(lit("travail depuis la maison")))
        | lower(raw["description"]).contains(lower(lit("travail depuis votre domicile")))
        | lower(raw["description"]).contains(lower(lit("travail depuis le domicile")))
        | lower(raw["description"]).contains(lower(lit("travail en remote")))
        | lower(raw["description"]).contains(lower(lit("travail en télétravail")))
        | lower(raw["description"]).contains(lower(lit("travail en teletravail")))
        | lower(raw["description"]).contains(lower(lit("travail en distanciel")))
        | lower(raw["description"]).contains(lower(lit("travail à domicile")))
        | lower(raw["description"]).contains(lower(lit("travail a domicile")))
        | lower(raw["description"]).contains(lower(lit("travail depuis n'importe où")))
        | lower(raw["description"]).contains(lower(lit("travail depuis n'importe ou")))
        | lower(raw["description"]).contains(lower(lit("travail depuis partout")))
        | lower(raw["description"]).contains(lower(lit("travail depuis votre lieu de vie")))
        | lower(raw["description"]).contains(lower(lit("travail depuis votre lieu de residence")))
        | lower(raw["description"]).contains(lower(lit("travail depuis votre residence")))
        | lower(raw["description"]).contains(lower(lit("travail depuis votre maison")))
        | lower(raw["description"]).contains(lower(lit("travail depuis votre foyer")))
        | lower(raw["description"]).contains(lower(lit("travail depuis votre chez vous")))
        
    )

    # Sur site
    is_site = (
        lower(dim_teletravail["type_teletravail"]) == lit("sur site")
    ) & (
        lower(raw["description"]).contains(lower(lit("sur site")))
        | lower(raw["description"]).contains(lower(lit("présentiel")))
        | lower(raw["description"]).contains(lower(lit("presentiel")))
        | lower(raw["description"]).contains(lower(lit("au bureau")))
        | lower(raw["description"]).contains(lower(lit("dans nos locaux")))
        | lower(raw["description"]).contains(lower(lit("dans nos bureaux")))
        | lower(raw["description"]).contains(lower(lit("dans notre siège")))
        | lower(raw["description"]).contains(lower(lit("dans notre siege")))
        | lower(raw["description"]).contains(lower(lit("dans nos locaux")))
        | lower(raw["description"]).contains(lower(lit("dans nos bureaux")))
        | lower(raw["description"]).contains(lower(lit("dans notre siège")))
        | lower(raw["description"]).contains(lower(lit("dans notre siege")))
        | lower(raw["description"]).contains(lower(lit("dans nos locaux")))
        | lower(raw["description"]).contains(lower(lit("dans nos bureaux")))
        | lower(raw["description"]).contains(lower(lit("dans notre siège")))
        | lower(raw["description"]).contains(lower(lit("dans notre siege")))
        | lower(raw["description"]).contains(lower(lit("dans nos locaux")))
        | lower(raw["description"]).contains(lower(lit("dans nos bureaux")))
        | lower(raw["description"]).contains(lower(lit("dans notre siège")))
        | lower(raw["description"]).contains(lower(lit("dans notre siege")))
        | lower(raw["description"]).contains(lower(lit("dans nos locaux")))
        | lower(raw["description"]).contains(lower(lit("dans nos bureaux")))
        | lower(raw["description"]).contains(lower(lit("dans notre siège")))
        | lower(raw["description"]).contains(lower(lit("dans notre siege")))
        | lower(raw["description"]).contains(lower(lit("dans nos locaux")))
        | lower(raw["description"]).contains(lower(lit("dans nos bureaux")))
        | lower(raw["description"]).contains(lower(lit("dans notre siège")))
        | lower(raw["description"]).contains(lower(lit("dans notre siege")))
        | lower(raw["description"]).contains(lower(lit("dans nos locaux")))
        | lower(raw["description"]).contains(lower(lit("dans nos bureaux")))
        | lower(raw["description"]).contains(lower(lit("dans notre siège")))
        | lower(raw["description"]).contains(lower(lit("dans notre siege")))
        | lower(raw["description"]).contains(lower(lit("dans nos locaux")))
        | lower(raw["description"]).contains(lower(lit("dans nos bureaux")))
        | lower(raw["description"]).contains(lower(lit("dans notre siège")))
        | lower(raw["description"]).contains(lower(lit("dans notre siege")))
        | lower(raw["description"]).contains(lower(lit("dans nos locaux")))
        | lower(raw["description"]).contains(lower(lit("dans nos bureaux")))
        | lower(raw["description"]).contains(lower(lit("dans notre siège")))
        | lower(raw["description"]).contains(lower(lit("dans notre siege")))
        | lower(raw["description"]).contains(lower(lit("dans nos locaux")))
        | lower(raw["description"]).contains(lower(lit("dans nos bureaux")))
        | lower(raw["description"]).contains(lower(lit("dans notre siège")))
        | lower(raw["description"]).contains(lower(lit("dans notre siege")))
        | lower(raw["description"]).contains(lower(lit("dans nos locaux")))
        | lower(raw["description"]).contains(lower(lit("dans nos bureaux")))
        | lower(raw["description"]).contains(lower(lit("dans notre siège")))
        | lower(raw["description"]).contains(lower(lit("dans notre siege")))
    )

    # Hybride
    is_hybride = (
        lower(dim_teletravail["type_teletravail"]) == lit("hybride")
    ) & (
        lower(raw["description"]).contains(lower(lit("hybride")))
        | lower(raw["description"]).contains(lower(lit("mixte")))
        | lower(raw["description"]).contains(lower(lit("flexible")))
        | lower(raw["description"]).contains(lower(lit("2-3 jours")))
        | lower(raw["description"]).contains(lower(lit("2 à 3 jours")))
        | lower(raw["description"]).contains(lower(lit("2 a 3 jours")))
        | lower(raw["description"]).contains(lower(lit("2/3 jours")))
        | lower(raw["description"]).contains(lower(lit("2 ou 3 jours")))
        | lower(raw["description"]).contains(lower(lit("2-3 jours par semaine")))
        | lower(raw["description"]).contains(lower(lit("2 à 3 jours par semaine")))
        | lower(raw["description"]).contains(lower(lit("2 a 3 jours par semaine")))
        | lower(raw["description"]).contains(lower(lit("2/3 jours par semaine")))
        | lower(raw["description"]).contains(lower(lit("2 ou 3 jours par semaine")))
        | lower(raw["description"]).contains(lower(lit("2-3 jours de télétravail")))
        | lower(raw["description"]).contains(lower(lit("2 à 3 jours de télétravail")))
        | lower(raw["description"]).contains(lower(lit("2 a 3 jours de télétravail")))
        | lower(raw["description"]).contains(lower(lit("2/3 jours de télétravail")))
        | lower(raw["description"]).contains(lower(lit("2 ou 3 jours de télétravail")))
        | lower(raw["description"]).contains(lower(lit("2-3 jours de teletravail")))
        | lower(raw["description"]).contains(lower(lit("2 à 3 jours de teletravail")))
        | lower(raw["description"]).contains(lower(lit("2 a 3 jours de teletravail")))
        | lower(raw["description"]).contains(lower(lit("2/3 jours de teletravail")))
        | lower(raw["description"]).contains(lower(lit("2 ou 3 jours de teletravail")))
        | lower(raw["description"]).contains(lower(lit("2-3 jours de remote")))
        | lower(raw["description"]).contains(lower(lit("2 à 3 jours de remote")))
        | lower(raw["description"]).contains(lower(lit("2 a 3 jours de remote")))
        | lower(raw["description"]).contains(lower(lit("2/3 jours de remote")))
        | lower(raw["description"]).contains(lower(lit("2 ou 3 jours de remote")))
        | lower(raw["description"]).contains(lower(lit("2-3 jours de télétravail par semaine")))
        | lower(raw["description"]).contains(lower(lit("2 à 3 jours de télétravail par semaine")))
        | lower(raw["description"]).contains(lower(lit("2 a 3 jours de télétravail par semaine")))
        | lower(raw["description"]).contains(lower(lit("2/3 jours de télétravail par semaine")))
        | lower(raw["description"]).contains(lower(lit("2 ou 3 jours de télétravail par semaine")))
        | lower(raw["description"]).contains(lower(lit("2-3 jours de teletravail par semaine")))
        | lower(raw["description"]).contains(lower(lit("2 à 3 jours de teletravail par semaine")))
        | lower(raw["description"]).contains(lower(lit("2 a 3 jours de teletravail par semaine")))
        | lower(raw["description"]).contains(lower(lit("2/3 jours de teletravail par semaine")))
        | lower(raw["description"]).contains(lower(lit("2 ou 3 jours de teletravail par semaine")))
        | lower(raw["description"]).contains(lower(lit("2-3 jours de remote par semaine")))
        | lower(raw["description"]).contains(lower(lit("2 à 3 jours de remote par semaine")))
        | lower(raw["description"]).contains(lower(lit("2 a 3 jours de remote par semaine")))
        | lower(raw["description"]).contains(lower(lit("2/3 jours de remote par semaine")))
        | lower(raw["description"]).contains(lower(lit("2 ou 3 jours de remote par semaine")))
        | lower(raw["description"]).contains(lower(lit("2-3 jours de télétravail par semaine")))
        | lower(raw["description"]).contains(lower(lit("2 à 3 jours de télétravail par semaine")))
        | lower(raw["description"]).contains(lower(lit("2 a 3 jours de télétravail par semaine")))
        | lower(raw["description"]).contains(lower(lit("2/3 jours de télétravail par semaine")))
        | lower(raw["description"]).contains(lower(lit("2 ou 3 jours de télétravail par semaine")))
        | lower(raw["description"]).contains(lower(lit("2-3 jours de teletravail par semaine")))
        | lower(raw["description"]).contains(lower(lit("2 à 3 jours de teletravail par semaine")))
        | lower(raw["description"]).contains(lower(lit("2 a 3 jours de teletravail par semaine")))
        | lower(raw["description"]).contains(lower(lit("2/3 jours de teletravail par semaine")))
        | lower(raw["description"]).contains(lower(lit("2 ou 3 jours de teletravail par semaine")))
        | lower(raw["description"]).contains(lower(lit("2-3 jours de remote par semaine")))
        | lower(raw["description"]).contains(lower(lit("2 à 3 jours de remote par semaine")))
        | lower(raw["description"]).contains(lower(lit("2 a 3 jours de remote par semaine")))
        | lower(raw["description"]).contains(lower(lit("2/3 jours de remote par semaine")))
        | lower(raw["description"]).contains(lower(lit("2 ou 3 jours de remote par semaine")))
    )

    # 3) Condition de jointure
    join_cond = (
        exact_match_raw | partial_match_raw
        | is_distance | is_site | is_hybride
    )

    # 4) Join et flags
    df = (
        raw.join(dim_teletravail, join_cond, how="left")
           .select(
               raw["id_offre"].alias("id_offre"),
               raw["ID_LOCAL"].alias("id_local"),
               dim_teletravail["id_teletravail"].alias("id_teletravail"),
               when(exact_match_raw,   lit(1)).otherwise(lit(0)).alias("is_exact"),
               when(partial_match_raw, lit(1)).otherwise(lit(0)).alias("is_partial"),
               when(is_distance,       lit(1)).otherwise(lit(0)).alias("is_distance_regex"),
               when(is_site,           lit(1)).otherwise(lit(0)).alias("is_site_regex"),
               when(is_hybride,        lit(1)).otherwise(lit(0)).alias("is_hybride_regex")
           )
    )

    # 5) Fenêtre de priorisation
    w = Window.partition_by("id_local").order_by(
        col("is_exact")        .desc(),
        col("is_partial")      .desc(),
        col("is_distance_regex").desc(),
        col("is_site_regex")   .desc(),
        col("is_hybride_regex").desc()
    )

    best = (
        df.with_column("rn", row_number().over(w))
          .filter(col("rn") == 1)
          .drop("is_exact", "is_partial",
                "is_distance_regex", "is_site_regex",
                "is_hybride_regex", "rn")
    )

    return best 