# Guide d'utilisation de l'Infrastructure JobMarket 🚀

Ce guide détaillé vous aidera à comprendre et utiliser l'infrastructure JobMarket, même si vous débutez avec Docker et les services conteneurisés.

## Pour les débutants 🎯

Si vous découvrez le projet, suivez ces étapes simples :

### Première utilisation 1️⃣

1. Ouvrez votre terminal
2. Rendez le script de gestion utilisable :

    ```bash
    chmod +x manage-jobmarket.sh
    ```

3. Initialisez le projet (ETL/ELT) :

    ```bash
    ./manage-jobmarket.sh init
    ```

    Cette étape va :
    - Exécuter l'ETL Snowflake pour charger les données
    - Exécuter DBT pour transformer les données
    - Préparer l'environnement pour le reste des services

4. Démarrez l'environnement complet :

    ```bash
    ./manage-jobmarket.sh start development
    ```

5. Attendez que tout démarre (cela peut prendre quelques minutes la première fois)
6. Ouvrez votre navigateur et accédez à :
    - `http://localhost:8080` pour voir le dashboard
    - `http://localhost:8081/docs` pour voir l'API
    - `http://localhost:5010` pour voir MLflow

### Commandes essentielles pour débuter ❓

```bash
# Initialiser le projet (à faire une seule fois)
./manage-jobmarket.sh init

# Démarrer les services
./manage-jobmarket.sh start development

# Voir si tout fonctionne
./manage-jobmarket.sh status

# Voir les messages d'erreur si quelque chose ne marche pas
./manage-jobmarket.sh logs

# Tout arrêter
./manage-jobmarket.sh stop
```

### Si quelque chose ne marche pas 🔍

1. Vérifiez que Docker est bien démarré
2. Si l'initialisation échoue :

    ```bash
    # Nettoyez l'environnement
    ./manage-jobmarket.sh clean

    # Réinitialisez le projet
    ./manage-jobmarket.sh init
    ```

3. Si les services ne démarrent pas :

    ```bash
    ./manage-jobmarket.sh clean
    ./manage-jobmarket.sh start development
    ```

4. Regardez les logs pour comprendre le problème :

    ```bash
    # Tous les logs
    ./manage-jobmarket.sh logs

    # Logs spécifiques
    ./manage-jobmarket.sh logs jm-elt-snowflake
    ./manage-jobmarket.sh logs jm-elt-dbt
    ```

## Guide complet 📚

### Les différents modes de démarrage 🛠

#### 0. Initialisation (requis avant premier démarrage)

```bash
./manage-jobmarket.sh init
```

- Exécute l'ETL Snowflake
- Exécute les transformations DBT
- Prépare les données pour l'application

#### 1. Mode développement complet (recommandé pour débuter)

```bash
./manage-jobmarket.sh start development
```

- Démarre tout (frontend, backend, MLflow)
- Idéal pour tester l'application

#### 2. Mode frontend uniquement

```bash
./manage-jobmarket.sh start frontend
```

- Démarre juste l'interface utilisateur
- Utile pour travailler sur le dashboard

#### 3. Mode entraînement

```bash
./manage-jobmarket.sh start training
```

- Pour entraîner des modèles ML
- Inclut MLflow et ses dépendances

### Les services et leurs ports 📊

| Service       | Port | URL                   | Description            |
| ------------- | ---- | --------------------- | ---------------------- |
| ETL Snowflake | -    | -                     | Chargement des données |
| DBT           | -    | -                     | Transformation données |
| Frontend      | 8080 | http://localhost:8080 | Dashboard              |
| Backend       | 8081 | http://localhost:8081 | API                    |
| MLflow        | 5010 | http://localhost:5010 | Suivi des modèles      |
| Model Serving | 8000 | http://localhost:8000 | Déploiement modèles    |

### Gestion des logs 📝

Les logs sont essentiels pour comprendre ce qui se passe :

```bash
# Tous les logs
./manage-jobmarket.sh logs

# Logs des services ETL
./manage-jobmarket.sh logs jm-elt-snowflake
./manage-jobmarket.sh logs jm-elt-dbt

# Logs des services principaux
./manage-jobmarket.sh logs frontend
./manage-jobmarket.sh logs backend
```

### Cycle de vie des services 🔄

1. **Démarrage propre**

    ```bash
    ./manage-jobmarket.sh start development
    ```

2. **Vérification**

    ```bash
    ./manage-jobmarket.sh status
    ```

3. **Arrêt propre**

    ```bash
    ./manage-jobmarket.sh stop
    ```

4. **Nettoyage complet**

    ```bash
    ./manage-jobmarket.sh clean
    ```

### Services optionnels 🎛

#### 1. Monitoring (Prometheus)

```bash
./manage-jobmarket.sh start monitoring
```

- Accès : `http://localhost:9090`
- Utile pour surveiller les performances

#### 2. Base de données PostgreSQL

```bash
./manage-jobmarket.sh start postgres
```

- Port : 5432
- Alternative à SQLite pour plus de performance

#### 3. Cache Redis

```bash
./manage-jobmarket.sh start cache
```

- Port : 6379
- Améliore les performances avec du cache

## Résolution des problèmes courants 🚨

### 1. "Erreur lors de l'initialisation"

- **Symptôme** : L'ETL ou DBT échoue pendant l'initialisation
- **Solution** :
  1. Vérifiez les credentials Snowflake dans `.env`
  2. Regardez les logs spécifiques :

      ```bash
      ./manage-jobmarket.sh logs jm-elt-snowflake
      ./manage-jobmarket.sh logs jm-elt-dbt
      ```

  3. Nettoyez et réessayez :

      ```bash
      ./manage-jobmarket.sh clean
      ./manage-jobmarket.sh init
      ```

### 2. "Docker n'est pas démarré"

- **Symptôme** : `Error: Docker is not running`
- **Solution** :
  1. Ouvrez Docker Desktop
  2. Attendez qu'il soit complètement démarré
  3. Réessayez votre commande

### 3. "Ports déjà utilisés"

- **Symptôme** : `Error: Ports are already allocated`
- **Solution** :
  1. Arrêtez les services existants :

      ```bash
      ./manage-jobmarket.sh stop
      ```

  2. Vérifiez qu'aucune autre application n'utilise ces ports
  3. Redémarrez les services

### 4. "Mémoire insuffisante"

- **Symptôme** : `Error: Insufficient memory`
- **Solution** :
  1. Ouvrez Docker Desktop
  2. Allez dans Paramètres > Resources
  3. Augmentez la mémoire (minimum 8GB recommandé)

## Astuces et bonnes pratiques 💡

1. **Toujours vérifier l'état avant de commencer**

    ```bash
    ./manage-jobmarket.sh status
    ```

2. **Nettoyer régulièrement si vous avez des problèmes**

    ```bash
    ./manage-jobmarket.sh clean
    ```

3. **Garder un œil sur les logs en développement**

    ```bash
    ./manage-jobmarket.sh logs
    ```

4. **Redémarrer proprement en cas de doute**

    ```bash
    ./manage-jobmarket.sh stop
    ./manage-jobmarket.sh start development
    ```

## Notes importantes 📝

- L'initialisation (`init`) n'est nécessaire qu'une seule fois ou après un `clean`
- Les données ETL sont transformées lors de l'initialisation
- Les données MLflow sont sauvegardées même après un arrêt
- Modifiez les fichiers `.env` pour changer les configurations
- Utilisez `clean` avec précaution car cela supprime les données

## Besoin d'aide ? 🆘

1. Vérifiez les logs pour comprendre le problème
2. Consultez la section résolution des problèmes ci-dessus
3. Assurez-vous que Docker a assez de ressources
4. Essayez un redémarrage propre des services
