#!/usr/bin/env python3
"""
Script de test pour le modèle déployé de prédiction de la demande de pommes
Utilise l'endpoint REST du service ml-model pour faire des prédictions
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import json
import argparse
import sys
from train_model import (
    generate_synthetic_apple_data,
    add_feature_engineering,
    prepare_features,
)


def prepare_prediction_data(n_samples=10, random_seed=42):
    """Prépare un échantillon de données pour la prédiction"""
    print(f"🔧 Preparing prediction data...")

    # Générer des données synthétiques
    df = generate_synthetic_apple_data(n_samples=n_samples, random_seed=random_seed)

    # Sauvegarder la variable cible avant de la supprimer
    y_true = df["apple_demand"].values if "apple_demand" in df.columns else None

    # Colonnes attendues par le modèle
    expected_columns = [
        "year",
        "month",
        "day_of_year",
        "day_of_week",
        "week_of_year",
        "quarter",
        "temperature",
        "humidity",
        "rainfall",
        "sunshine_hours",
        "apple_price",
        "economic_index",
        "is_weekend",
        "trend",
        "season_fall",
        "season_spring",
        "season_summer",
        "season_winter",
        "holiday_back_to_school",
        "holiday_normal",
        "holiday_summer_holidays",
        "holiday_winter_holidays",
    ]

    # Vérifier les colonnes manquantes
    missing_columns = [col for col in expected_columns if col not in df.columns]
    if missing_columns:
        print(f"⚠️ Colonnes manquantes: {missing_columns}")
        # Ajouter les colonnes manquantes avec des valeurs par défaut
        for col in missing_columns:
            if col.startswith("season_"):
                df[col] = False
            elif col.startswith("holiday_"):
                df[col] = False
            else:
                df[col] = 0

    # Sélectionner uniquement les colonnes attendues
    df = df[expected_columns]

    # Convertir les types de données selon le schéma attendu
    type_mapping = {
        "year": "int64",
        "month": "int64",
        "day_of_year": "int64",
        "day_of_week": "int64",
        "week_of_year": "int64",
        "quarter": "int64",
        "temperature": "float64",
        "humidity": "float64",
        "rainfall": "float64",
        "sunshine_hours": "float64",
        "apple_price": "float64",
        "economic_index": "float64",
        "is_weekend": "int64",
        "trend": "float64",
        "season_fall": "bool",
        "season_spring": "bool",
        "season_summer": "bool",
        "season_winter": "bool",
        "holiday_back_to_school": "bool",
        "holiday_normal": "bool",
        "holiday_summer_holidays": "bool",
        "holiday_winter_holidays": "bool",
    }

    for col, dtype in type_mapping.items():
        df[col] = df[col].astype(dtype)

    # Convertir en format compatible avec l'API
    instances = df.to_dict(orient="records")

    print(f"✅ Prediction data prepared:")
    print(f"   Number of instances: {len(instances)}")
    print(f"   Number of features: {len(instances[0])}")
    print(f"   Features: {list(instances[0].keys())}")

    # Vérifier les types de données
    print("\n📊 Data types verification:")
    sample = instances[0]
    for col, val in sample.items():
        print(f"   {col}: {type(val).__name__} = {val}")

    return instances, y_true


def predict_demand(instances, model_endpoint="http://localhost:8000/invocations"):
    """Envoie les données à l'endpoint de prédiction et récupère les résultats"""
    print(f"🚀 Sending prediction request to {model_endpoint}...")

    try:
        # Format pour MLflow 2.22.0 - Liste de dictionnaires (records)
        data = {"dataframe_records": instances}

        # Configuration de la requête
        headers = {
            "Content-Type": "application/json",
        }

        # Afficher un aperçu des données envoyées
        print("\n📤 Request payload preview:")
        preview = {
            "dataframe_records": instances[:2],
            "schema": {
                "columns": list(instances[0].keys()),
                "sample_types": {
                    col: type(instances[0][col]).__name__
                    for col in list(instances[0].keys())
                },
            },
            "total_records": len(instances),
        }
        print(json.dumps(preview, indent=2))

        # Envoyer la requête
        response = requests.post(model_endpoint, data=json.dumps(data), headers=headers)

        # Vérifier la réponse
        if response.status_code == 200:
            predictions = response.json()
            print(f"✅ Predictions received successfully!")
            return predictions
        else:
            print(f"❌ Error getting predictions: {response.status_code}")
            print(f"Response: {response.text}")
            print("\n🔍 Debug information:")
            print(f"Request headers: {headers}")
            print(f"Schema attendu vs envoyé:")
            expected_cols = set(
                [
                    "year",
                    "month",
                    "day_of_year",
                    "day_of_week",
                    "week_of_year",
                    "quarter",
                    "temperature",
                    "humidity",
                    "rainfall",
                    "sunshine_hours",
                    "apple_price",
                    "economic_index",
                    "is_weekend",
                    "trend",
                    "season_fall",
                    "season_spring",
                    "season_summer",
                    "season_winter",
                    "holiday_back_to_school",
                    "holiday_normal",
                    "holiday_summer_holidays",
                    "holiday_winter_holidays",
                ]
            )
            sent_cols = set(instances[0].keys())
            print("   Colonnes manquantes:", expected_cols - sent_cols)
            print("   Colonnes en trop:", sent_cols - expected_cols)
            return None

    except Exception as e:
        print(f"❌ Error during prediction request: {str(e)}")
        print("\n🔍 Debug information:")
        print(f"Data type: {type(data)}")
        print(f"First record example:")
        print(json.dumps(instances[0], indent=2))
        return None


def evaluate_predictions(y_true, y_pred):
    """Évalue les prédictions par rapport aux vraies valeurs"""
    if y_true is None:
        print("\n⚠️ Pas de valeurs réelles disponibles pour l'évaluation")
        return None

    from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

    print("\n📊 Prediction Evaluation:")
    print(f"   RMSE: {rmse:.2f}")
    print(f"   MAE: {mae:.2f}")
    print(f"   R²: {r2:.4f}")
    print(f"   MAPE: {mape:.2f}%")

    return {"rmse": rmse, "mae": mae, "r2": r2, "mape": mape}


def display_predictions(y_true, y_pred, n_display=5):
    """Affiche une comparaison des prédictions vs valeurs réelles"""
    print(f"\n🔍 Sample Predictions (first {n_display}):")
    print(f"{'True':>10} {'Predicted':>10} {'Diff':>10} {'Error %':>10}")
    print("-" * 45)

    for true, pred in zip(y_true[:n_display], y_pred[:n_display]):
        diff = pred - true
        error_pct = (diff / true) * 100
        print(f"{true:10.2f} {pred:10.2f} {diff:10.2f} {error_pct:10.2f}%")


def main():
    parser = argparse.ArgumentParser(
        description="Test deployed apple demand prediction model"
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        default="http://localhost:8000/invocations",
        help="Model serving endpoint URL",
    )
    parser.add_argument(
        "--n-samples", type=int, default=10, help="Number of test samples to generate"
    )
    parser.add_argument(
        "--random-seed", type=int, default=42, help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--display-samples",
        type=int,
        default=5,
        help="Number of prediction samples to display",
    )

    args = parser.parse_args()

    try:
        print("🎯 Starting Model Prediction Test")
        print(f"Endpoint: {args.endpoint}")
        print(f"Samples: {args.n_samples}")

        # Préparer les données de test
        instances, y_true = prepare_prediction_data(
            n_samples=args.n_samples, random_seed=args.random_seed
        )

        # Faire les prédictions
        response = predict_demand(instances, model_endpoint=args.endpoint)

        if response is not None:
            y_pred = np.array(response["predictions"])

            # Afficher les prédictions
            print("\n🔍 Predictions:")
            print(f"   Shape: {y_pred.shape}")
            print(f"   Mean: {y_pred.mean():.2f}")
            print(f"   Std: {y_pred.std():.2f}")
            print(f"   Min: {y_pred.min():.2f}")
            print(f"   Max: {y_pred.max():.2f}")

            # Évaluer si possible
            if y_true is not None:
                metrics = evaluate_predictions(y_true, y_pred)
                display_predictions(y_true, y_pred, n_display=args.display_samples)
            else:
                print(
                    "\n⚠️ Mode prédiction uniquement (pas de valeurs réelles pour comparaison)"
                )
                print("\n🔍 Sample Predictions:")
                for i, pred in enumerate(y_pred[: args.display_samples]):
                    print(f"   Sample {i+1}: {pred:.2f}")

            print("\n✅ Prediction test completed successfully!")
        else:
            print("\n❌ Prediction test failed!")
            sys.exit(1)

    except Exception as e:
        print(f"\n💥 Error during prediction test: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
