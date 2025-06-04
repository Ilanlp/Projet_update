from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

# Arguments par défaut pour le DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Fonction Python d'exemple
def print_hello():
    return "Hello from Airflow!"

# Création du DAG
with DAG(
    'example_dag',
    default_args=default_args,
    description='Un DAG d\'exemple simple',
    schedule_interval=timedelta(days=1),
    start_date=days_ago(1),
    tags=['example'],
) as dag:

    # Tâche 1: Exécuter une commande bash
    t1 = BashOperator(
        task_id='print_date',
        bash_command='date',
    )

    # Tâche 2: Exécuter une fonction Python
    t2 = PythonOperator(
        task_id='print_hello',
        python_callable=print_hello,
    )

    # Tâche 3: Exécuter une commande bash avec un sleep
    t3 = BashOperator(
        task_id='sleep',
        bash_command='sleep 5',
    )

    # Définir l'ordre d'exécution des tâches
    t1 >> t2 >> t3 