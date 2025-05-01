# models/src/matched_contrat_py_copy.py

from snowflake.snowpark.functions import (
    lower
)
from snowflake.snowpark.window import Window

def model(dbt, session):
    raw         = session.table("RAW.RAW_SOFTSKILL")
    dim         = session.table("SILVER.DIM_SOFTSKILL")
    
    exact_match = lower(raw["SUMMARY"]) == lower(dim["SUMMARY"])
   
    
    

    # Création de la condition de jointure
    join_cond = exact_match

    # Jointure avec les tables
    df = (
        raw.join(dim, join_cond, how="left")
           .select(
               raw["ID_ROME"],
               dim['ID_SOFTSKILL'],
               raw["SCORE"]

           )
    )

    return df
