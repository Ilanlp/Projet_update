from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.sensors.filesystem import FileSensor
from airflow.operators.docker_operator import DockerOperator
from docker.types import Mount

path = "/Users/maikimike/Documents/datascientest/data-engineer/mar25_bootcamp_de_job_market"

with DAG(
    dag_id="load_jobmarket",
    tags=["jobmarket", "docker", "datascientest"],
    default_args={
        "owner": "airflow",
        "start_date": days_ago(0, minute=1),
    },
    schedule_interval="0 17 * * *",
    catchup=False,
) as dag:
    # jobmarket_sensor = FileSensor(
    #     task_id='jobmarket_sensor',
    #     filepath='data/all_jobs.csv',
    #     poke_interval=20,
    #     timeout=120,
    #     mode='poke'
    # )
    run_extract_offers = DockerOperator(
        task_id="run_extract_offers",
        image="jm-etl-normalizer:latest",
        # api_version="auto",
        auto_remove=True,
        # command='python3 normalizer.py',
        mounts=[
            Mount(
                source=f"{path}/pipeline/src/.env",
                target="/app/.env",
                type="bind",
                read_only=True,
            ),
            Mount(
                source=f"{path}/data",
                target="/app/data",
                type="bind",
                read_only=False,
            ),
        ],
    )
    run_load_offers = DockerOperator(
        task_id="run_load_offers",
        image="jm-elt-snowflake:latest",
        api_version="auto",
        auto_remove=True,
        # network_mode="jm_network",
        command="python3 offre.py",
        mounts=[
            Mount(
                source=f"{path}/pipeline/src/.env",
                target="/usr/src/snowflake/.env",
                type="bind",
                read_only=True,
            ),
            Mount(
                source=f"{path}/data",
                target="/usr/src/data",
                type="bind",
                read_only=False,
            ),
        ],
    )
    run_transform_offers = DockerOperator(
        task_id="run_transform_offers",
        image="jm-elt-dbt:latest",
        auto_remove=True,
        mounts=[
            Mount(
                source=f"{path}/snowflake/DBT/.env",
                target="/usr/src/DBT/Projet_DBT/.env",
                type="bind",
                read_only=True,
            ),
        ],
    )
    run_extract_offers >> run_load_offers >> run_transform_offers
