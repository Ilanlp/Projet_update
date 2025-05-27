# Execution ELT

## Lancer d'abord le service jm-elt-snowflake 
docker-compose -f docker-compose_ELT.init.yaml up --build jm-elt-snowflake

## Lancer ensuite le service jm-elt-dbt 
docker-compose -f docker-compose_ELT.init.yaml up --build jm-elt-dbt