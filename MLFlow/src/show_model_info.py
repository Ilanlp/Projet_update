#!/usr/bin/env python3
"""Script pour afficher les informations détaillées d'un modèle MLflow."""

import mlflow
import sys
import os


def show_model_info(model_name):
    """
    Affiche les informations détaillées d'un modèle MLflow.

    Args:
        model_name (str): Nom du modèle à inspecter
    """
    try:
        # Configuration de MLflow
        tracking_uri = os.environ.get(
            "MLFLOW_TRACKING_URI", "http://mlflow-tracking:5000"
        )
        mlflow.set_tracking_uri(tracking_uri)
        print(f"Using tracking URI: {tracking_uri}")

        # Récupération des versions du modèle
        client = mlflow.tracking.MlflowClient()
        versions = client.search_model_versions(f"name='{model_name}'")

        if not versions:
            print(f"No versions found for model '{model_name}'")
            return

        print(f"\nModel Information for: {model_name}")
        print("=" * 50)

        for version in versions:
            print(f"\nVersion: {version.version}")
            print(f"Stage: {version.current_stage}")
            print(f"Run ID: {version.run_id}")

            # Récupération des métriques du run
            run = client.get_run(version.run_id)
            if run.data.metrics:
                print("Metrics:")
                for key, value in run.data.metrics.items():
                    print(f"  {key}: {value}")

            # Affichage des tags
            if version.tags:
                print("Tags:")
                for key, value in version.tags.items():
                    print(f"  {key}: {value}")

            # Status et timestamp
            print(f"Status: {version.status}")
            if version.creation_timestamp:
                from datetime import datetime

                timestamp = datetime.fromtimestamp(version.creation_timestamp / 1000.0)
                print(f"Created: {timestamp}")

            print("-" * 30)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main():
    if len(sys.argv) != 2:
        print("Usage: python show_model_info.py MODEL_NAME")
        sys.exit(1)

    show_model_info(sys.argv[1])


if __name__ == "__main__":
    main()
