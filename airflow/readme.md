# Airflow installation

## DOCKER COMPOSE

[https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html]

```bash
# Fetching docker-compose.yaml
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/3.0.1/docker-compose.yaml'

# Setting the right Airflow user
mkdir -p ./dags ./logs ./plugins ./config
echo -e "AIRFLOW_UID=$(id -u)" > .env

# Initialize airflow.cfg (Optional)
docker compose run airflow-cli airflow config list

# Initialize the database
docker compose up airflow-init

# Running Airflow
docker compose up

# Running the CLI commands
docker compose run airflow-worker airflow info

# If you have Linux or Mac OS, you can make your work easier and download a optional wrapper scripts that will allow you to run commands with a simpler command.
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/3.0.1/airflow.sh'
chmod +x airflow.sh

./airflow.sh info
# You can also use bash as parameter to enter interactive bash shell in the container or python to enter python container.
./airflow.sh bash
./airflow.sh python

# Accessing the web interface
# http://localhost:8080

# Sending requests to the REST API
ENDPOINT_URL="http://localhost:8080/"
curl -X GET  \
    --user "airflow:airflow" \
    "${ENDPOINT_URL}/api/v1/pools"

# Cleaning up
docker compose down --volumes --rmi all
```

## Cleaning-up the environment

The best way to do this is to:

* Run docker `compose down --volumes --remove-orphans` command in the directory you downloaded the `docker-compose.yaml` file
* Remove the entire directory where you downloaded the `docker-compose.yaml` file `rm -rf '<DIRECTORY>'`
* Run through this guide from the very beginning, starting by re-downloading the `docker-compose.yaml` file

## K8S

[https://airflow.apache.org/docs/helm-chart/stable/index.html]

```bash
# Installing the Chart
helm repo add apache-airflow https://airflow.apache.org
helm upgrade --install airflow apache-airflow/airflow --namespace airflow --create-namespace

# Upgrading the Chart
helm upgrade airflow apache-airflow/airflow --namespace airflow

# Uninstalling the Chart
helm delete airflow --namespace airflow

# Installing the Chart with Argo CD, Flux, Rancher or Terraform

```

### Installing the Chart with Argo CD, Flux, Rancher or Terraform

```bash

```
