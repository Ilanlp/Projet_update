# Initialise l'application

* générer les datas de référence des API dans `./data` via appel API
* génèrer la tables RAW / DIM dans `./data` via `init.py`
* execution du script etl.py pour injection dans le stage snowflake

```bash
cd pipeline/src

# générer les datas de référence des API dans `./data` via appel API
python -m adzuna.references
python -m france_travail.references

# génèrer la tables RAW / DIM dans `./data`
python init.py

# injection dans le stage snowflake
python etl.py
```
