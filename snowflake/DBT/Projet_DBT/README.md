# Welcome to your new dbt project

## Using the starter project

### ETAPES 

1. **Run the “raw” layer**
-dbt run --select bronze

2. **Run the “silver” layer**
-dbt run --select silver

3. **Run the “gold” layer**
#Faire tourner fait_offre les les 2 tables de liaisons qui ne dépendent pas de fait offre
-dbt run --select fait_offre  liaison_Rome_Metier_gold_sql liaison_Rome_Metier_gold_sql

#Faire tourner la table de liaison offre_Competence qui dépend de l'id de fait_offre
-dbt run --select liaison_Offre_Competence






