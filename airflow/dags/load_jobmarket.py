from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.sensors.filesystem import FileSensor
from airflow.operators.docker_operator import DockerOperator
from docker.types import Mount
import os

path = os.getenv("PROJECT_PATH")


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
    run_extract_offers = DockerOperator(
        task_id="run_extract_offers",
        image="jm-etl-normalizer:latest",
        auto_remove=True,
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
        mount_tmp_dir=False,
        api_version="auto",
        auto_remove=True,
        command="python3 offre.py",
        mounts=[
            Mount(
                source=f"{path}/pipeline/src/snowflake",
                target="/usr/src/snowflake",
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
                source=f"{path}/snowflake/DBT/Projet_DBT",
                target="/usr/src/DBT/Projet_DBT",
                type="bind",
                read_only=False,
            ),
        ],
    )
    run_extract_offers >> run_load_offers >> run_transform_offers
