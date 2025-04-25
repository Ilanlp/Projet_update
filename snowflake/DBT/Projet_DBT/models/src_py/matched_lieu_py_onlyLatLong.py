# models/src/matched_lieu.py

from snowflake.snowpark.functions import (
    col,
    sin, cos, sqrt, radians, asin,
    lit, when, row_number
)
from snowflake.snowpark.window import Window

# Ne conserve que le matching géographique (coordonnées) et la distance

def model(dbt, session):
    raw      = session.table("RAW.ANALYSES")
    dim_lieu = session.table("PUBLIC.DIM_LIEU")

    # 1. Calcul Haversine
    lat1 = radians(raw["latitude"])
    lon1 = radians(raw["longitude"])
    lat2 = radians(dim_lieu["latitude"])
    lon2 = radians(dim_lieu["longitude"])
    dlat = lat1 - lat2
    dlon = lon1 - lon2
    a    = sin(dlat/2)**2 + cos(lat2) * cos(lat1) * sin(dlon/2)**2
    c    = 2 * asin(sqrt(a))
    distance_km = lit(6371) * c

    # 2. Condition de matching géographique : < 10 km
    coord_match = distance_km < lit(10)

    # 3. LEFT JOIN pour conserver toutes les lignes de RAW
    df = (
        raw
        .join(dim_lieu, coord_match, how="left")
        .select(
            raw["id"].alias("id"),
            raw["id_local"].alias("id_local"),
            raw["location_name"].alias("location_name"),
            raw["latitude"].alias("latitude"),
            raw["longitude"].alias("longitude"),

            dim_lieu["id_lieu"].alias("id_lieu"),
            dim_lieu["ville"].alias("ville"),

            when(coord_match, 1).otherwise(0).alias("is_coord"),
            distance_km.alias("distance_km")
        )
    )

    # 4. Fenêtre pour ne garder que le meilleur (géographique) par id
    w = Window.partition_by("id_local").order_by(
        col("is_coord").desc(),      # priorise les vrais matchs
        col("distance_km").asc()     # puis la distance la plus petite
    )

    best = (
        df
        .with_column("rn", row_number().over(w))
        .filter(col("rn") == 1)
        .drop("is_coord", "distance_km", "rn")
    )

    return best
