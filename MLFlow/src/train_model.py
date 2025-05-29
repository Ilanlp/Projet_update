#!/usr/bin/env python3
"""
Script d'entraînement de modèle ML avec génération de données synthétiques
Basé sur train_model.py - Aucune donnée externe requise
"""

import mlflow
import mlflow.sklearn
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler, LabelEncoder
import argparse
import os
import sys
from datetime import datetime, timedelta
import joblib
import json
import warnings

warnings.filterwarnings("ignore")


def setup_mlflow(tracking_uri, experiment_name):
    """Configuration de MLflow"""
    print(f"🔧 Setting up MLflow...")
    print(f"   Tracking URI: {tracking_uri}")
    print(f"   Experiment: {experiment_name}")

    mlflow.set_tracking_uri(tracking_uri)

    try:
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment is None:
            experiment_id = mlflow.create_experiment(experiment_name)
            print(f"✅ Created new experiment: {experiment_name}")
        else:
            experiment_id = experiment.experiment_id
            print(f"✅ Using existing experiment: {experiment_name}")

        mlflow.set_experiment(experiment_name)
        return experiment_id

    except Exception as e:
        print(f"❌ Error setting up MLflow: {e}")
        raise


def generate_synthetic_apple_data(n_samples=2000, random_seed=42):
    """
    Génération de données synthétiques réalistes pour la prédiction de demande de pommes
    """
    print(f"🍎 Generating synthetic apple demand data...")
    print(f"   Samples: {n_samples}")
    print(f"   Random seed: {random_seed}")

    np.random.seed(random_seed)

    # Génération des dates sur 2 ans
    start_date = datetime(2022, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(n_samples)]

    # Features temporelles
    data = {
        "date": dates,
        "year": [d.year for d in dates],
        "month": [d.month for d in dates],
        "day_of_year": [d.timetuple().tm_yday for d in dates],
        "day_of_week": [d.weekday() for d in dates],  # 0=Lundi, 6=Dimanche
        "week_of_year": [d.isocalendar()[1] for d in dates],
        "quarter": [(d.month - 1) // 3 + 1 for d in dates],
    }

    # Features météorologiques (avec saisonnalité)
    seasonal_temp = 15 + 10 * np.sin(2 * np.pi * np.array(data["day_of_year"]) / 365.25)
    data["temperature"] = seasonal_temp + np.random.normal(0, 5, n_samples)

    seasonal_humidity = 60 + 20 * np.sin(
        2 * np.pi * (np.array(data["day_of_year"]) - 90) / 365.25
    )
    data["humidity"] = np.clip(
        seasonal_humidity + np.random.normal(0, 10, n_samples), 20, 90
    )

    # Précipitations (plus en hiver)
    rainfall_base = 2 + 3 * np.sin(
        2 * np.pi * (np.array(data["day_of_year"]) - 180) / 365.25
    )
    data["rainfall"] = np.clip(
        np.random.exponential(np.maximum(rainfall_base, 0.5)), 0, 50
    )

    # Ensoleillement (inverse des précipitations)
    data["sunshine_hours"] = np.clip(
        8
        + 4 * np.sin(2 * np.pi * np.array(data["day_of_year"]) / 365.25)
        - 0.1 * data["rainfall"]
        + np.random.normal(0, 1, n_samples),
        2,
        14,
    )

    # Features économiques
    base_price = 2.5
    price_trend = 0.0001 * np.arange(n_samples)  # Inflation légère
    seasonal_price = 0.3 * np.sin(2 * np.pi * np.array(data["day_of_year"]) / 365.25)
    data["apple_price"] = (
        base_price + price_trend + seasonal_price + np.random.normal(0, 0.2, n_samples)
    )

    # Indice économique (simulé)
    data["economic_index"] = 100 + np.cumsum(np.random.normal(0, 0.5, n_samples))

    # Features catégorielles
    seasons = []
    holidays = []
    for d in dates:
        # Saison
        if d.month in [12, 1, 2]:
            seasons.append("winter")
        elif d.month in [3, 4, 5]:
            seasons.append("spring")
        elif d.month in [6, 7, 8]:
            seasons.append("summer")
        else:
            seasons.append("fall")

        # Vacances/Événements (simplifié)
        if d.month == 12 or d.month == 1:  # Fêtes de fin d'année
            holidays.append("winter_holidays")
        elif d.month in [7, 8]:  # Vacances d'été
            holidays.append("summer_holidays")
        elif d.month == 9:  # Rentrée
            holidays.append("back_to_school")
        else:
            holidays.append("normal")

    data["season"] = seasons
    data["holiday_period"] = holidays
    data["is_weekend"] = [1 if d >= 5 else 0 for d in data["day_of_week"]]

    # Features de tendance
    data["trend"] = np.arange(n_samples) / n_samples  # Tendance linéaire

    # Création de la variable cible : demande de pommes
    # Modèle complexe mais réaliste
    base_demand = 50  # Demande de base

    # Effets saisonniers (plus de pommes en automne/hiver)
    seasonal_effect = 20 * np.array(
        [
            (
                2.0
                if s == "fall"
                else 1.5 if s == "winter" else 0.8 if s == "spring" else 0.6
            )
            for s in seasons
        ]
    )

    # Effet week-end (plus de demande)
    weekend_effect = 10 * np.array(data["is_weekend"])

    # Effet météo
    weather_effect = (
        -0.3 * (data["temperature"] - 20) ** 2  # Optimal vers 20°C
        + -0.1 * data["rainfall"]  # Moins de ventes quand il pleut
        + 0.5 * np.array(data["sunshine_hours"])  # Plus de ventes au soleil
    )

    # Effet prix (élasticité négative)
    price_effect = -15 * (np.array(data["apple_price"]) - base_price)

    # Effet économique
    economic_effect = 0.1 * (np.array(data["economic_index"]) - 100)

    # Effet vacances
    holiday_effect = np.array(
        [
            (
                25
                if h == "winter_holidays"
                else (
                    15 if h == "summer_holidays" else 10 if h == "back_to_school" else 0
                )
            )
            for h in holidays
        ]
    )

    # Effet jour de la semaine
    weekday_effect = np.array(
        [
            (
                5
                if d in [4, 5]  # Vendredi, Samedi
                else 3 if d in [3, 6] else 0  # Jeudi, Dimanche
            )
            for d in data["day_of_week"]
        ]
    )

    # Tendance temporelle
    trend_effect = 10 * data["trend"]

    # Bruit aléatoire
    noise = np.random.normal(0, 8, n_samples)

    # Assemblage final
    apple_demand = (
        base_demand
        + seasonal_effect
        + weekend_effect
        + weather_effect
        + price_effect
        + economic_effect
        + holiday_effect
        + weekday_effect
        + trend_effect
        + noise
    )

    # S'assurer que la demande est positive
    data["apple_demand"] = np.maximum(apple_demand, 5)

    # Création du DataFrame
    df = pd.DataFrame(data)

    # Encoding des variables catégorielles
    df = pd.get_dummies(
        df, columns=["season", "holiday_period"], prefix=["season", "holiday"]
    )

    print(f"✅ Synthetic data generated successfully!")
    print(f"   Shape: {df.shape}")
    print(
        f"   Target range: {df['apple_demand'].min():.1f} - {df['apple_demand'].max():.1f}"
    )
    print(f"   Target mean: {df['apple_demand'].mean():.1f}")
    print(f"   Features: {[col for col in df.columns if col != 'apple_demand']}")

    return df


def add_feature_engineering(df):
    """Ajout de features engineering avancées"""
    print("🔧 Adding feature engineering...")

    # Features de lag (demande passée)
    df = df.sort_values("date").reset_index(drop=True)

    # Lags simples
    for lag in [1, 7, 30]:
        df[f"demand_lag_{lag}"] = df["apple_demand"].shift(lag)

    # Moyennes mobiles
    for window in [7, 14, 30]:
        df[f"demand_ma_{window}"] = (
            df["apple_demand"].rolling(window=window, min_periods=1).mean()
        )
        df[f"temp_ma_{window}"] = (
            df["temperature"].rolling(window=window, min_periods=1).mean()
        )

    # Features cycliques
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    df["day_of_year_sin"] = np.sin(2 * np.pi * df["day_of_year"] / 365.25)
    df["day_of_year_cos"] = np.cos(2 * np.pi * df["day_of_year"] / 365.25)

    # Interactions importantes
    df["temp_humidity_interaction"] = df["temperature"] * df["humidity"] / 100
    df["price_economic_interaction"] = df["apple_price"] * df["economic_index"] / 100

    # Volatilité des prix
    df["price_volatility"] = df["apple_price"].rolling(window=30, min_periods=1).std()

    # Supprimer les NaN dus aux lags
    df = df.fillna(method="bfill").fillna(method="ffill")

    print(f"✅ Feature engineering completed!")
    print(f"   New shape: {df.shape}")

    return df


def prepare_features(df, target_column="apple_demand"):
    """Préparation des features avec nettoyage"""
    print(f"🔧 Preparing features...")

    # Supprimer les colonnes non nécessaires pour l'entraînement
    columns_to_drop = ["date"]  # Garder les autres features temporelles

    df_model = df.drop(columns=[col for col in columns_to_drop if col in df.columns])

    # Séparation features/target
    if target_column not in df_model.columns:
        raise ValueError(f"Target column '{target_column}' not found in data")

    X = df_model.drop(columns=[target_column])
    y = df_model[target_column]

    print(f"✅ Features prepared:")
    print(f"   Features shape: {X.shape}")
    print(f"   Target shape: {y.shape}")
    print(
        f"   Feature columns: {list(X.columns)[:10]}..."
        if len(X.columns) > 10
        else f"   Feature columns: {list(X.columns)}"
    )

    return X, y


def train_model(X, y, hyperparameter_tuning=True, cv_folds=3):
    """Entraînement du modèle avec MLflow tracking"""

    with mlflow.start_run() as run:
        print(f"🚀 Starting training run: {run.info.run_id}")

        # Split des données
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=True
        )

        # Log des informations sur les données
        mlflow.log_param("n_samples", len(X))
        mlflow.log_param("n_features", X.shape[1])
        mlflow.log_param("test_size", 0.2)
        mlflow.log_param("random_state", 42)
        mlflow.log_param("data_type", "synthetic")

        # Configuration du modèle
        if hyperparameter_tuning:
            print("🔍 Performing hyperparameter tuning...")

            param_grid = {
                "n_estimators": [100, 200],
                "max_depth": [10, 15, 20],
                "min_samples_split": [2, 5],
                "min_samples_leaf": [1, 2],
                "max_features": ["sqrt", "log2"],
            }

            rf = RandomForestRegressor(random_state=42, n_jobs=-1)
            grid_search = GridSearchCV(
                rf,
                param_grid,
                cv=cv_folds,
                scoring="neg_mean_squared_error",
                n_jobs=-1,
                verbose=1,
            )

            print("   Training with cross-validation...")
            grid_search.fit(X_train, y_train)
            model = grid_search.best_estimator_

            # Log des meilleurs hyperparamètres
            for param, value in grid_search.best_params_.items():
                mlflow.log_param(f"best_{param}", value)

            mlflow.log_metric("cv_best_score", -grid_search.best_score_)
            mlflow.log_param("cv_folds", cv_folds)

        else:
            print("🔧 Training with optimized default parameters...")
            model = RandomForestRegressor(
                n_estimators=200,
                max_depth=15,
                min_samples_split=2,
                min_samples_leaf=1,
                max_features="sqrt",
                random_state=42,
                n_jobs=-1,
            )
            model.fit(X_train, y_train)

            # Log des paramètres
            for param, value in model.get_params().items():
                mlflow.log_param(param, value)

        # Prédictions et métriques
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)

        # Calcul des métriques
        train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)
        train_mae = mean_absolute_error(y_train, y_pred_train)
        test_mae = mean_absolute_error(y_test, y_pred_test)

        # Métriques business (pourcentage d'erreur)
        train_mape = np.mean(np.abs((y_train - y_pred_train) / y_train)) * 100
        test_mape = np.mean(np.abs((y_test - y_pred_test) / y_test)) * 100

        # Log des métriques
        mlflow.log_metric("train_rmse", train_rmse)
        mlflow.log_metric("test_rmse", test_rmse)
        mlflow.log_metric("train_r2", train_r2)
        mlflow.log_metric("test_r2", test_r2)
        mlflow.log_metric("train_mae", train_mae)
        mlflow.log_metric("test_mae", test_mae)
        mlflow.log_metric("train_mape", train_mape)
        mlflow.log_metric("test_mape", test_mape)

        # Feature importance
        feature_importance = pd.DataFrame(
            {"feature": X.columns, "importance": model.feature_importances_}
        ).sort_values("importance", ascending=False)

        # Log des top features
        for i, (_, row) in enumerate(feature_importance.head(10).iterrows()):
            mlflow.log_metric(
                f"feature_importance_{i+1}_{row['feature']}", row["importance"]
            )

        # Log des informations sur l'entraînement
        mlflow.log_param("algorithm", "RandomForestRegressor")
        mlflow.log_param("training_time", datetime.now().isoformat())
        mlflow.log_param("feature_engineering", "advanced")

        # Sauvegarde du modèle avec MLflow
        model_info = mlflow.sklearn.log_model(
            model,
            "apple_demand_model",
            registered_model_name=None,
            signature=mlflow.models.infer_signature(X_train, y_pred_train),
        )

        # Log de la feature importance en tant qu'artefact
        importance_file = "feature_importance.csv"
        feature_importance.to_csv(importance_file, index=False)
        mlflow.log_artifact(importance_file)
        os.remove(importance_file)

        print(f"✅ Model trained successfully!")
        print(f"   Train RMSE: {train_rmse:.2f}")
        print(f"   Test RMSE: {test_rmse:.2f}")
        print(f"   Train R²: {train_r2:.4f}")
        print(f"   Test R²: {test_r2:.4f}")
        print(f"   Test MAPE: {test_mape:.2f}%")
        print(f"   Model artifact path: {model_info.model_uri}")
        print(f"   Top 5 features: {feature_importance.head()['feature'].tolist()}")

        return model, run.info.run_id, model_info.model_uri


def register_model(model_uri, model_name, stage="Staging"):
    """Enregistrement du modèle dans MLflow Registry"""
    print(f"📝 Registering model in MLflow Registry...")
    print(f"   Model URI: {model_uri}")
    print(f"   Model Name: {model_name}")

    try:
        model_version = mlflow.register_model(model_uri, model_name)

        print(f"✅ Model registered successfully!")
        print(f"   Model Name: {model_version.name}")
        print(f"   Version: {model_version.version}")
        print(f"   Source: {model_version.source}")

        # Transition vers un stage
        if stage:
            client = mlflow.tracking.MlflowClient()
            client.transition_model_version_stage(
                name=model_name, version=model_version.version, stage=stage
            )
            print(f"✅ Model transitioned to stage: {stage}")

        return model_version

    except Exception as e:
        print(f"❌ Error registering model: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description="Train ML model with synthetic data")
    parser.add_argument(
        "--n-samples",
        type=int,
        default=2000,
        help="Number of synthetic samples to generate",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="apple_demand_predictor",
        help="Name for model registration",
    )
    parser.add_argument(
        "--experiment-name",
        type=str,
        default="apple_demand_synthetic",
        help="MLflow experiment name",
    )
    parser.add_argument(
        "--tracking-uri",
        type=str,
        default="http://mlflow-tracking:5000",
        help="MLflow tracking URI",
    )
    parser.add_argument(
        "--target-column", type=str, default="apple_demand", help="Target column name"
    )
    parser.add_argument(
        "--no-hyperparameter-tuning",
        action="store_true",
        help="Skip hyperparameter tuning",
    )
    parser.add_argument(
        "--register", action="store_true", help="Register model in MLflow Registry"
    )
    parser.add_argument(
        "--stage",
        type=str,
        default="Staging",
        choices=["Staging", "Production", "Archived"],
        help="Model stage for registration",
    )
    parser.add_argument(
        "--cv-folds", type=int, default=3, help="Number of cross-validation folds"
    )
    parser.add_argument(
        "--feature-engineering",
        action="store_true",
        help="Apply advanced feature engineering",
    )
    parser.add_argument(
        "--random-seed", type=int, default=42, help="Random seed for reproducibility"
    )

    args = parser.parse_args()

    try:
        print("🎯 Starting ML Training Pipeline with Synthetic Data")
        print(f"Samples: {args.n_samples}")
        print(f"Model name: {args.model_name}")
        print(f"Experiment: {args.experiment_name}")
        print(f"Tracking URI: {args.tracking_uri}")
        print(f"Random seed: {args.random_seed}")

        # Configuration MLflow
        experiment_id = setup_mlflow(args.tracking_uri, args.experiment_name)

        # Génération des données synthétiques
        df = generate_synthetic_apple_data(args.n_samples, args.random_seed)

        # Feature engineering optionnel
        if args.feature_engineering:
            df = add_feature_engineering(df)

        # Préparation des features
        X, y = prepare_features(df, args.target_column)

        # Entraînement
        model, run_id, model_uri = train_model(
            X,
            y,
            hyperparameter_tuning=not args.no_hyperparameter_tuning,
            cv_folds=args.cv_folds,
        )

        # Enregistrement optionnel
        if args.register:
            model_version = register_model(model_uri, args.model_name, args.stage)
            print(
                f"🏆 Training completed! Model {args.model_name} v{model_version.version} ready for serving"
            )
        else:
            print(f"🏆 Training completed! Run ID: {run_id}")
            print(
                f"To register: mlflow models register -m '{model_uri}' -n '{args.model_name}'"
            )

        print(f"\n🔗 View results:")
        print(f"   MLflow UI: {args.tracking_uri}")
        print(f"   Experiment: {args.experiment_name}")
        print(f"   Run ID: {run_id}")

    except Exception as e:
        print(f"💥 Training failed: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
