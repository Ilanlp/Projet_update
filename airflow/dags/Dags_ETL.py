from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.dates import days_ago
from docker.types import Mount
import os

# Définition des arguments par défaut pour la DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Création de la DAG
dag = DAG(
    'etl_pipeline',
    default_args=default_args,
    description='ETL Pipeline pour JobMarket',
    schedule_interval=timedelta(days=1),
    start_date=days_ago(1),
    catchup=False,
    tags=['jobmarket', 'etl'],
)

# Tâche de début
start = DummyOperator(
    task_id='start',
    dag=dag,
)

# Tâche ETL Normalizer
normalizer = DockerOperator(
    task_id='etl_normalizer',
    image='ilanlp/jm-etl-normalizer:latest',
    container_name='jm-etl-normalizer',
    docker_url='unix://var/run/docker.sock',
    api_version='auto',
    auto_remove=True,
    environment={
        'ADZUNA_APP_ID': os.getenv('ADZUNA_APP_ID'),
        'ADZUNA_APP_KEY': os.getenv('ADZUNA_APP_KEY'),
        'FRANCE_TRAVAIL_ID': os.getenv('FRANCE_TRAVAIL_ID'),
        'FRANCE_TRAVAIL_KEY': os.getenv('FRANCE_TRAVAIL_KEY'),
        'SEARCH_TERMS': os.getenv('SEARCH_TERMS'),
        'CATEGORY_ADZUNA': os.getenv('CATEGORY_ADZUNA'),
        'CODE_ROME2': os.getenv('CODE_ROME2'),
        'CODE_ROME': os.getenv('CODE_ROME'),
        'LOCATION_ADZUNA': os.getenv('LOCATION_ADZUNA'),
        'LOCATION_FRANCE_TRAVAIL': os.getenv('LOCATION_FRANCE_TRAVAIL'),
        'MAX_RESULTS_PER_SOURCE': os.getenv('MAX_RESULTS_PER_SOURCE'),
        'MAX_DAYS_OLD': os.getenv('MAX_DAYS_OLD'),
        'OUTPUT_DIR': '/app/data',
    },
    dag=dag,
)

# Tâche ETL Snowflake
snowflake = DockerOperator(
    task_id='etl_snowflake',
    image='jm-elt-snowflake:latest',
    container_name='jm-elt-snowflake',
    api_version='auto',
    auto_remove=True,
    docker_url='unix://var/run/docker.sock',
    network_mode='jm_network',
    mounts=[
        Mount(source='./pipeline/src/.env', target='/usr/src/.env', type='bind', read_only=True),
        Mount(source='./pipeline/src/snowflake', target='/usr/src/snowflake', type='bind', read_only=False),
        Mount(source='./pipeline/src/data', target='/usr/src/data', type='bind', read_only=False),
    ],
    dag=dag,
)

# Tâche DBT
dbt = DockerOperator(
    task_id='etl_dbt',
    image='jm-elt-dbt:latest',
    container_name='jm-elt-dbt',
    api_version='auto',
    auto_remove=True,
    docker_url='unix://var/run/docker.sock',
    network_mode='jm_network',
    user='node',  # Comme dans votre Dockerfile DBT
    mounts=[
        Mount(source='./snowflake/DBT/.env', target='/usr/src/DBT/.env', type='bind', read_only=True),
        Mount(source='./snowflake/DBT', target='/usr/src/DBT', type='bind', read_only=False),
    ],
    dag=dag,
)

# Tâche de fin
end = DummyOperator(
    task_id='end',
    dag=dag,
)

# Définition de l'ordre d'exécution des tâches
start >> normalizer >> snowflake >> dbt >> end 