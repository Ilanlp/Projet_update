# Welcome to your new dbt project

## Using the starter project

### créer un env et installer les dépendances

```bash
```

### init Snowflake

```bash
```

### init dbt

allez dans votre "nano ~/.dbt/profiles.yml" puis crée le profil avec le même nom de profil que celui dans votre fichier dbt_project.yml!

```bash
nano ~/.dbt/profiles.yml
```

### seed dbt ???

```bash
# dbt seed (pour charger vos tables dans snowflake)
dbt seed
```

3- Allez dans snowflake pour mettre les tables dans les bons schémas etc...
4- Tronquez la tables "analyses" pour pouvoir faires vos matching (2000 lignes est pas mal pour un matching rapide)
5- Initialisation du projet : mettez les bons paramètres (schéma, nom de table , sources... ) dans dbt_project.yml et model/src_py/sources.yml

6- Faites tournez vos matching dimensions avec : 

dbt run select dbt run --select matched_lieu_py
dbt run select dbt run --select matched_contrat_py


puis faites tourner le tout :  dbt run select dbt run --select matched_contrat_py matched_lieu_py fait_offres_py.py


ATTENTION : 

si vous mettez "dbt run" directement sans granulariser (avec "dbt run --select") ca ne va pas marcher car il faut un ordre de passage. 
