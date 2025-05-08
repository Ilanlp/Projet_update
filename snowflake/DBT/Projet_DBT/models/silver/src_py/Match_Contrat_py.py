# models/src/matched_contrat_py_copy.py

from snowflake.snowpark.functions import (
    col, lower, lit, when, row_number
)
from snowflake.snowpark.window import Window

def model(dbt, session):
    raw         = session.table("RAW.RAW_OFFRE")
    dim_contrat = session.table("SILVER.DIM_CONTRAT")

    # 1) Matchings exact & partiel
    exact_match_raw   = lower(raw["contract_type"]) \
                        .contains(lower(dim_contrat["type_contrat"]))
    partial_match_raw = lower(raw["description"]) \
                        .contains(lower(dim_contrat["type_contrat"]))

    # 2) Matching permissif par mots-clés avec contains()

    # Freelance  
    is_freelance = (
        lower(dim_contrat["type_contrat"]) == lit("freelance")
    ) & (
        lower(raw["description"]).contains(lower(lit("libéral")))
        | lower(raw["description"]).contains(lower(lit("liberal")))
        | lower(raw["description"]).contains(lower(lit("indépendant")))
        | lower(raw["description"]).contains(lower(lit("independant")))
        | lower(raw["description"]).contains(lower(lit("auto-entrepreneur")))
        | lower(raw["description"]).contains(lower(lit("auto entrepreneur")))
        | lower(raw["description"]).contains(lower(lit("portage salarial")))
        | lower(raw["contract_type"]).contains(lower(lit("freelance")))
        | lower(raw["contract_type"]).contains(lower(lit("liberal")))
        | lower(raw["contract_type"]).contains(lit("libéral"))
        | lower(raw["contract_duration"]).contains(lower(lit("franchise")))
    )

    # CDI  
    is_cdi = (
        lower(dim_contrat["type_contrat"]) == lit("cdi")
    ) & (
        lower(raw["description"]).contains(lit("cdi"))
        | lower(raw["description"]).contains(lower(lit("durée indéterminée")))
        | lower(raw["description"]).contains(lower(lit("contrat à durée indéterminée")))
        | lower(raw["description"]).contains(lower(lit("permanent")))
        | lower(raw["description"]).contains(lower(lit("embauche")))
        | lower(raw["description"]).contains(lower(lit("poste permanent")))
        | lower(raw["contract_type"]).contains(lit("cdi"))
        | lower(raw["contract_duration"]).contains(lower(lit("Contrat à durée indéterminée")))
        | lower(raw["contract_duration"]).contains(lower(lit("cdi")))
    )

    # CDD  
    is_cdd = (
        lower(dim_contrat["type_contrat"]) == lit("cdd")
    ) & (
        lower(raw["description"]).contains(lit("cdd"))
        | lower(raw["description"]).contains(lit("durée déterminée"))
        | lower(raw["description"]).contains(lit("contrat à durée déterminée"))
        | lower(raw["description"]).contains(lit("mission de"))
        | lower(raw["contract_type"]).contains(lit("cdd"))
        | lower(raw["contract_duration"]).contains(lower(lit("CDD")))
        | lower(raw["contract_duration"]).contains(lower(lit("Contrat à durée déterminée")))
    )

    # Intérim  
    is_interim = (
        lower(dim_contrat["type_contrat"]).isin(lit("intérim"), lit("interim"))
    ) & (
        lower(raw["description"]).contains(lit("intérim"))
        | lower(raw["description"]).contains(lit("intérimaire"))
        | lower(raw["description"]).contains(lit("interim"))
        | lower(raw["description"]).contains(lit("temporaire"))
        | lower(raw["description"]).contains(lit("travail temporaire"))
        | lower(raw["description"]).contains(lit("agence d'intérim"))
        | lower(raw["contract_type"]).contains(lit("intérim"))
        | lower(raw["contract_type"]).contains(lit("interim"))
        | lower(raw["contract_duration"]).contains(lit("intérim"))
        | lower(raw["contract_duration"]).contains(lit("intérimaire"))
    )

    # Alternance
    is_alternance = (
        lower(dim_contrat["type_contrat"]) == lit("alternance")
    ) & (
        lower(raw["description"]).contains(lower(lit("alternance")))
        | lower(raw["description"]).contains(lower(lit("apprentissage")))
        | lower(raw["description"]).contains(lower(lit("contrat d'apprentissage")))
        | lower(raw["description"]).contains(lower(lit("contrat de professionnalisation")))
    )

    # Stage
    is_stage = (
        lower(dim_contrat["type_contrat"]) == lit("stage")
    ) & (
        lower(raw["description"]).contains(lower(lit("stage")))
        | lower(raw["description"]).contains(lower(lit("internship")))
        | lower(raw["description"]).contains(lower(lit("stagiaire")))
        | lower(raw["description"]).contains(lower(lit("stage de fin d'études")))
    )

    # 3) Condition de jointure
    join_cond = (
        exact_match_raw | partial_match_raw
        | is_freelance | is_cdi | is_cdd | is_interim
        | is_alternance | is_stage
    )

    # 4) Join et flags
    df = (
        raw.join(dim_contrat, join_cond, how="left")
           .select(
               raw["id"].alias("id"),
               raw["ID_LOCAL"].alias("id_local"),
               dim_contrat["id_contrat"].alias("id_contrat"),
               dim_contrat["type_contrat"].alias("type_contrat"),
               raw["CONTRACT_TYPE"].alias("contract_type"),
               raw["CONTRACT_DURATION"].alias("contract_duration"),
               when(exact_match_raw,   lit(1)).otherwise(lit(0)).alias("is_exact"),
               when(partial_match_raw, lit(1)).otherwise(lit(0)).alias("is_partial"),
               when(is_freelance,      lit(1)).otherwise(lit(0)).alias("is_freelance"),
               when(is_cdi,            lit(1)).otherwise(lit(0)).alias("is_cdi_regex"),
               when(is_cdd,            lit(1)).otherwise(lit(0)).alias("is_cdd_regex"),
               when(is_interim,        lit(1)).otherwise(lit(0)).alias("is_interim_regex"),
               when(is_alternance,     lit(1)).otherwise(lit(0)).alias("is_alternance_regex"),
               when(is_stage,          lit(1)).otherwise(lit(0)).alias("is_stage_regex")
           )
    )

    # 5) Fenêtre de priorisation
    w = Window.partition_by("id_local").order_by(
        col("is_exact")        .desc(),
        col("is_partial")      .desc(),
        col("is_alternance_regex").desc(),
        col("is_stage_regex")  .desc(),
        col("is_cdi_regex")    .desc(),
        col("is_cdd_regex")    .desc(),
        col("is_interim_regex").desc(),
        col("is_freelance")    .desc()
    )

    best = (
        df.with_column("rn", row_number().over(w))
          .filter(col("rn") == 1)
          .drop("is_exact", "is_partial",
                "is_freelance", "is_cdi_regex",
                "is_cdd_regex", "is_interim_regex",
                "is_alternance_regex", "is_stage_regex",
                "rn")
    )

    return best
