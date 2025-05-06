# Jobmarket

## Initialisation

* générer les datas de référence des API dans `./data` via appel API
* génèrer la tables RAW / DIM dans `./data` via `init.py`
* initialiser Snowflake
* importer les données dans Snowflake

```bash
cd pipeline/src

# générer les datas de référence des API dans `./data` via appel API
python -m adzuna.references
python -m france_travail.references

# génèrer les csv RAW / DIM dans `./data`
python init_reference.py
# vérifier que vous avez tous les csv sinon déposer les dans `./data` > seed dbt

# initialiser Snowflake (Warehouse, Database, Shema, File format)
python snowflake/snowflake_init.py

# importer les données via stage dans Snowflake
python snowflake/snowflake_core.py
```

## Import incrémental des offres

```bash
python etl.py
# ... à finaliser
```
