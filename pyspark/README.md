# Guide complet d'Apache Spark dans Docker
## Analyse détaillée du docker-compose.yml et intégration avec VSCode

## Table des matières
1. [Introduction](#introduction)
2. [Architecture de la solution](#architecture-de-la-solution)
3. [Analyse du docker-compose.yml](#analyse-du-docker-composeyml)
   - [Version et services](#version-et-services)
   - [Service spark-master](#service-spark-master)
   - [Service spark-worker](#service-spark-worker)
   - [Service jupyter](#service-jupyter)
   - [Configuration du réseau](#configuration-du-réseau)
4. [Mise en place de l'environnement](#mise-en-place-de-lenvironnement)
5. [Intégration avec VSCode](#intégration-avec-vscode)
   - [Installation de l'extension](#installation-de-lextension)
   - [Connexion au conteneur](#connexion-au-conteneur)
   - [Configuration de l'environnement Python](#configuration-de-lenvironnement-python)
6. [Vérification et utilisation](#vérification-et-utilisation)
7. [Dépannage courant](#dépannage-courant)
8. [Bonnes pratiques](#bonnes-pratiques)

## Introduction

Ce document présente une analyse détaillée d'une configuration Docker Compose pour Apache Spark, permettant de déployer rapidement un cluster Spark composé d'un master, d'un worker, et d'un environnement de développement Jupyter avec intégration VSCode.

Apache Spark est un framework de traitement de données distribué puissant, conçu pour l'analyse de données à grande échelle. L'utilisation de Docker permet d'isoler l'environnement d'exécution et facilite le déploiement sur différentes machines.

## Architecture de la solution

La solution déployée comprend trois services principaux :
- **spark-master** : le nœud maître qui coordonne la distribution des tâches
- **spark-worker** : un nœud exécuteur qui traite les tâches
- **jupyter** : un environnement de développement avec PySpark préinstallé

Ces services sont interconnectés via un réseau Docker dédié, permettant une communication fluide entre les composants.

## Analyse du docker-compose.yml

### Version et services

```yaml
version: "3.2"
services:
```

- **version: "3.2"** : Spécifie la version de la syntaxe Docker Compose utilisée. La version 3.2 prend en charge les fonctionnalités modernes de Docker et est compatible avec Docker Swarm mode.
- **services** : Définit la section où les différents conteneurs sont spécifiés.

### Service spark-master

```yaml
spark-master:
  image: bitnami/spark:latest
  environment:
    - SPARK_MODE=master
  ports:
    - "8080:8080"  # Interface web Spark
    - "7077:7077"  # Port Spark master
  volumes:
    - ./data:/data
  networks:
    - spark-network
```

- **image: bitnami/spark:latest** : Utilise l'image Docker officielle de Bitnami pour Spark, dans sa version la plus récente. Cette image contient une installation préconfigurée de Spark.

- **environment:**
  - **SPARK_MODE=master** : Configure ce conteneur pour fonctionner en tant que nœud maître Spark. Le maître est responsable de la distribution des tâches aux workers et coordonne l'ensemble du cluster.

- **ports:**
  - **"8080:8080"** : Expose l'interface web de Spark Master sur le port 8080 de la machine hôte. Cette interface permet de surveiller l'état du cluster, les applications en cours d'exécution et les ressources disponibles.
  - **"7077:7077"** : Expose le port RPC (Remote Procedure Call) du Spark Master. Ce port est utilisé par les workers et les applications pour se connecter au master.

- **volumes:**
  - **./data:/data** : Monte le répertoire local `./data` vers le chemin `/data` dans le conteneur. Cela permet de partager des fichiers de données entre l'hôte et le conteneur.

- **networks:**
  - **spark-network** : Connecte ce service au réseau nommé `spark-network`, permettant la communication entre les conteneurs.

### Service spark-worker

```yaml
spark-worker:
  image: bitnami/spark:latest
  environment:
    - SPARK_MODE=worker
    - SPARK_MASTER_URL=spark://spark-master:7077
    - SPARK_WORKER_MEMORY=1G
  ports:
    - "8081:8081"  # Interface web du worker
  volumes:
    - ./data:/data
  depends_on:
    - spark-master
  networks:
    - spark-network
```

- **image: bitnami/spark:latest** : Utilise la même image que le master pour garantir la compatibilité.

- **environment:**
  - **SPARK_MODE=worker** : Configure ce conteneur en tant que worker Spark, chargé d'exécuter les tâches distribuées par le master.
  - **SPARK_MASTER_URL=spark://spark-master:7077** : Spécifie l'URL du master auquel le worker doit se connecter. Le nom d'hôte `spark-master` est résolu automatiquement par Docker dans le réseau partagé.
  - **SPARK_WORKER_MEMORY=1G** : Alloue 1 Go de mémoire au worker pour l'exécution des tâches Spark.

- **ports:**
  - **"8081:8081"** : Expose l'interface web du worker sur le port 8081 de l'hôte, permettant de surveiller son état.

- **volumes:**
  - **./data:/data** : Monte le même répertoire de données que le master, garantissant que les deux services ont accès aux mêmes fichiers.

- **depends_on:**
  - **spark-master** : Indique que ce service dépend du service `spark-master`. Docker Compose s'assurera que le master démarre avant le worker.

- **networks:**
  - **spark-network** : Connecte le worker au même réseau que le master.

### Service jupyter

```yaml
jupyter:
  image: jupyter/pyspark-notebook:latest
  ports:
    - "8888:8888"  # Interface Jupyter
  volumes:
    - ./notebooks:/home/jovyan/work
  environment:
    - SPARK_OPTS=--master=spark://spark-master:7077
  depends_on:
    - spark-master
  networks:
    - spark-network
```

- **image: jupyter/pyspark-notebook:latest** : Utilise l'image officielle Jupyter Notebook avec PySpark préinstallé.

- **ports:**
  - **"8888:8888"** : Expose l'interface web de Jupyter Notebook sur le port 8888 de l'hôte.

- **volumes:**
  - **./notebooks:/home/jovyan/work** : Monte le répertoire local `./notebooks` vers le répertoire de travail de l'utilisateur Jupyter. `jovyan` est l'utilisateur par défaut dans les images Jupyter.

- **environment:**
  - **SPARK_OPTS=--master=spark://spark-master:7077** : Configure PySpark pour se connecter automatiquement au Spark master à l'URL spécifiée.

- **depends_on:**
  - **spark-master** : Indique que Jupyter dépend du service `spark-master` et doit démarrer après lui.

- **networks:**
  - **spark-network** : Connecte Jupyter au même réseau que les autres services.

### Configuration du réseau

```yaml
networks:
  spark-network:
    driver: bridge
```

- **networks:** : Section définissant les réseaux Docker utilisés par les services.
- **spark-network:** : Nom du réseau utilisé par tous les services.
  - **driver: bridge** : Utilise le pilote de réseau bridge, qui est le pilote standard de Docker. Ce type de réseau permet aux conteneurs de communiquer entre eux tout en étant isolés des autres réseaux sur l'hôte.

## Mise en place de l'environnement

Avant de démarrer les conteneurs, assurez-vous de créer les répertoires nécessaires :

```bash
mkdir -p data notebooks
```

Ces répertoires seront montés dans les conteneurs et serviront à stocker respectivement les fichiers de données et les notebooks Jupyter.

Pour démarrer l'ensemble des services :

```bash
docker-compose up -d
```

L'option `-d` permet de démarrer les conteneurs en mode détaché (en arrière-plan).

Pour vérifier que les conteneurs sont en cours d'exécution :

```bash
docker ps
```

## Intégration avec VSCode

### Installation de l'extension

1. Ouvrez Visual Studio Code
2. Accédez à la vue Extensions (Ctrl+Shift+X ou Cmd+Shift+X)
3. Recherchez "Remote - Containers" (ID complet: `ms-vscode-remote.remote-containers`)
4. Cliquez sur "Installer"

Cette extension permet de se connecter à des conteneurs Docker et d'utiliser VSCode comme si vous travailliez directement dans l'environnement du conteneur.

### Connexion au conteneur

1. Dans VSCode, ouvrez la palette de commandes (F1 ou Ctrl+Shift+P)
2. Tapez "Remote-Containers: Attach to Running Container" et sélectionnez cette option
3. Une liste des conteneurs en cours d'exécution s'affiche
4. Sélectionnez le conteneur Jupyter (probablement nommé `[nom_du_projet]_jupyter_1`)
5. VSCode ouvrira une nouvelle fenêtre connectée au conteneur
6. Dans cette nouvelle fenêtre, ouvrez le dossier `/home/jovyan/work` qui correspond à votre répertoire local `./notebooks`

### Configuration de l'environnement Python

Une fois connecté au conteneur :

1. Dans la fenêtre VSCode connectée au conteneur, installez les extensions recommandées :
   - Python (ms-python.python)
   - Jupyter (ms-toolsai.jupyter)

2. Ouvrez ou créez un fichier notebook avec l'extension `.ipynb`

3. Lorsque vous ouvrez un notebook, sélectionnez le noyau Python qui a accès à PySpark

## Vérification et utilisation

Pour vérifier que tout fonctionne correctement :

1. Accédez à l'interface web Spark Master : http://localhost:8080
   - Vous devriez voir le master et un worker connecté

2. Accédez à l'interface web du Worker : http://localhost:8081
   - Vous pourrez voir les détails du worker

3. Accédez à Jupyter Notebook : http://localhost:8888
   - Vous aurez besoin d'un token d'authentification. Pour le trouver, exécutez :
     ```bash
     docker logs [nom_du_projet]_jupyter_1
     ```
   - Cherchez une ligne contenant "?token=..." dans les logs

4. Testez PySpark en créant un nouveau notebook et en exécutant :

```python
import pyspark
from pyspark.sql import SparkSession

# Créer une session Spark
spark = SparkSession.builder \
    .appName("Test Spark") \
    .getOrCreate()

# Afficher la version de Spark
print(f"Version de Spark : {spark.version}")

# Créer un DataFrame de test
df = spark.createDataFrame([
    (1, "John", 25),
    (2, "Alice", 30),
    (3, "Bob", 27)
], ["id", "name", "age"])

# Afficher le DataFrame
df.show()
```

## Dépannage courant

### Les conteneurs ne démarrent pas

Vérifiez les logs des conteneurs avec :
```bash
docker logs [nom_du_conteneur]
```

### Impossible de se connecter au Spark Master

- Vérifiez que le port 7077 est accessible
- Assurez-vous que le nom d'hôte `spark-master` est correctement résolu dans le réseau

### PySpark ne peut pas se connecter au Master

- Vérifiez la variable d'environnement `SPARK_OPTS`
- Assurez-vous que tous les conteneurs sont dans le même réseau

### Token Jupyter introuvable

Si vous ne trouvez pas le token dans les logs, vous pouvez exécuter :
```bash
docker exec -it [nom_du_projet]_jupyter_1 jupyter notebook list
```

## Bonnes pratiques

1. **Persistance des données** : Utilisez des volumes Docker nommés pour une meilleure persistance des données :
   ```yaml
   volumes:
     spark_data:
   ```
   Et référencez-les dans les services :
   ```yaml
   volumes:
     - spark_data:/data
   ```

2. **Évolutivité** : Pour ajouter plus de workers, vous pouvez utiliser la fonction `deploy` de Docker Compose :
   ```yaml
   spark-worker:
     deploy:
       replicas: 3
   ```

3. **Sécurité** : Pour un environnement de production, configurez l'authentification Spark et le chiffrement SSL.

4. **Ressources** : Ajustez les ressources allouées aux workers selon vos besoins :
   ```yaml
   environment:
     - SPARK_WORKER_MEMORY=2G
     - SPARK_WORKER_CORES=2
   ```

5. **Monitoring** : Intégrez des outils de monitoring comme Prometheus et Grafana pour surveiller votre cluster Spark.

6. **Sauvegarde des notebooks** : Assurez-vous de sauvegarder régulièrement vos notebooks en synchronisant le répertoire `./notebooks` avec un système de contrôle de version comme Git.