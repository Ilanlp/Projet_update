from snowflake.snowpark.functions import to_date, coalesce
from snowflake.snowpark.window import Window
from snowflake.snowpark.functions import row_number, col,lit
from snowflake.snowpark import Session
import datetime

def model(dbt, session: Session):
    # 1) Chargement des tables et alias
    today = datetime.date.today()
    raw = session.table("RAW.RAW_OFFRE").filter(
        col("DATE_EXTRACTION").cast("date") == today
    ).alias("r")
    dim_date = session.table("SILVER.DIM_DATE")

    dc = dim_date.alias("dc")   # pour DATE_CREATED
    du = dim_date.alias("du")   # pour DATE_UPDATED

    # 2) Jointure sur DIM_DATE
    joined = (
        raw
        .join(
            dc,
            to_date(raw["DATE_CREATED"]) == dc["id_date"],
            how="left"
        )
        .join(
            du,
            to_date(raw["DATE_UPDATED"]) == du["id_date"],
            how="left"
        )
    )

    # 3) (optionnel) Priorisation si vous avez plusieurs correspondances par id_local
    #    Sinon, vous pouvez sauter cette partie et retourner joined.select(...)
    w = Window.partition_by(raw["ID_LOCAL"]).order_by(
        # on pourrait prioriser par date_created la plus récente, par ex. :
        raw["DATE_CREATED"].desc()
    )
    best = (
        joined
        .with_column("rn", row_number().over(w))
        .filter(col("rn") == 1)
        .drop("rn")
    )

    default_date = lit("1900-01-01").cast("DATE")

    # 4) Sélection finale
    result = best.select(
        raw["id_offre"].alias("id_offre"),
        raw["ID_LOCAL"].alias("id_local"),
        # si dc.id_date est NULL, on prend 1900-01-01
        coalesce(dc["id_date"], default_date).alias("id_date_created"),
        # même chose pour date_updated
        coalesce(du["id_date"], default_date).alias("id_date_updated"),
        # ... ajoutez ici les autres colonnes si besoin ...
    
    )

    return result
