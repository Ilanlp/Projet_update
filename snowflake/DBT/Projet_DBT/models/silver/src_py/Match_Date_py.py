from snowflake.snowpark.functions import to_date
from snowflake.snowpark.window import Window
from snowflake.snowpark.functions import row_number, col
from snowflake.snowpark import Session

def model(dbt, session: Session):
    # 1) Chargement des tables et alias
    raw      = session.table("RAW.RAW_OFFRE").alias("r")
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

    # 4) Sélection finale
    result = best.select(
        raw["id"].alias("id"),
        raw["ID_LOCAL"].alias("id_local"),
        dc["id_date"].alias("id_date_created"),
        du["id_date"].alias("id_date_updated"),
    
    )

    return result
