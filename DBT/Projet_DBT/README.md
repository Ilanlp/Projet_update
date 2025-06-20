# Welcome to your new dbt project

## Using the starter project

### ETAPES

#### 1. **Run the “raw” layer**

```bash
dbt run --select bronze
```

#### 2. **Run the “silver” layer**

```bash
dbt run --select silver
```

#### 3. **Run the “gold” layer**

```bash
#Faire tourner fait_offre les les 2 tables de liaisons qui ne dépendent pas de fait offre
dbt run --select fait_offre  liaison_Rome_Metier_gold_sql liaison_Rome_Soft_Skill_gold_sql
```

```bash
# Faire tourner la table de liaison offre_Competence qui dépend de l'id de fait_offre
dbt run --select liaison_Offre_Competence
```
