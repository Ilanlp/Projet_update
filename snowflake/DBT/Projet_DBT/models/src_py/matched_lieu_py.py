# models/src/matched_lieu.py

from snowflake.snowpark.functions import (
    col, lower,
    sin, cos, sqrt, radians, asin,
    lit, when, row_number
)
from snowflake.snowpark.window import Window

def model(dbt, session):
    raw      = session.table("RAW.ANALYSES")
    dim_lieu = session.table("PUBLIC.DIM_LIEU")

    # 1. Conditions de matching textuel & géographique
    name_match   = lower(raw["location_name"]).contains(lower(dim_lieu["ville"]))
    dept_match   = lower(raw["location_name"]).contains(lower(dim_lieu["departement"]))
    region_match = lower(raw["location_name"]).contains(lower(dim_lieu["region"]))

    lat1 = radians(raw["latitude"]);  lon1 = radians(raw["longitude"])
    lat2 = radians(dim_lieu["latitude"]); lon2 = radians(dim_lieu["longitude"])
    dlat = lat1 - lat2; dlon = lon1 - lon2
    a    = sin(dlat/2)**2 + cos(lat2)*cos(lat1)*sin(dlon/2)**2
    c    = 2 * asin(sqrt(a))
    distance_km = lit(6371) * c
    coord_match = distance_km < lit(10)

    # 2. LEFT JOIN pour conserver toutes les lignes de RAW
    df = (
        raw
        .join(
            dim_lieu,
            name_match | dept_match | region_match | coord_match,
            how="left"
        )
        .select(
            raw["id"].alias("id"),
            raw["id_local"].alias("id_local"),
            #raw["description"].alias("description"),
            raw["location_name"].alias("location_name"),
            raw['latitude'].alias('latitude'),
            raw['longitude'].alias('longitude'),

            # colonnes de la dimension (NULL si pas de match)
            dim_lieu["id_lieu"].alias("id_lieu"),
            dim_lieu["ville"].alias("ville"),
            dim_lieu["latitude"].alias("dim_latitude"),
            dim_lieu["longitude"].alias("dim_longitude"),

            # flags (1/0) pour priorisation
            when(coord_match, 1).otherwise(0).alias("is_coord"),
            when(name_match,  1).otherwise(0).alias("is_name"),
            when(dept_match,  1).otherwise(0).alias("is_dept"),
            when(region_match,1).otherwise(0).alias("is_region"),

            # métriques pour départage
            distance_km.alias("distance_km"),
            dim_lieu["population"].alias("population")
        )
    )

    # 3. Fenêtre pour ne garder que le meilleur match par id,
    #    ou la ligne brute si aucun match (flags=0, distance_km=NULL)
    w = Window.partition_by("id_local").order_by(
        col("is_coord").desc(),      # 1) matching géographique
        col("distance_km").asc(),    #    + la plus petite distance
        col("is_name").desc(),       # 2) matching ville
        col("population").desc(),    #    + plus peuplée
        col("is_dept").desc(),       # 3) matching département
        col("population").desc(),    #    + plus peuplée
        col("is_region").desc(),     # 4) matching région
        col("population").desc()     #    + plus peuplée
    )

    best = (
        df
        .with_column("rn", row_number().over(w))
        .filter(col("rn") == 1)
        .drop("is_coord", "is_name", "is_dept", "is_region",
              "distance_km", "population", "rn")
    )

    return best



