import mlflow
import argparse
import sys
import os


def display_artifacts(client, run_id):
    """
    Display all artifacts in a run.

    Args:
        client: MLflow client
        run_id: ID of the run to inspect
    """
    artifacts = client.list_artifacts(run_id)
    print("\nAvailable artifacts:")
    for idx, artifact in enumerate(artifacts, 1):
        print(f"{idx}. {artifact.path} {'(dir)' if artifact.is_dir else '(file)'}")
        if artifact.is_dir:
            nested_artifacts = client.list_artifacts(run_id, artifact.path)
            for nested in nested_artifacts:
                print(f"   - {nested.path}")
    return artifacts


def select_model_path(artifacts):
    """
    Let user select which artifact directory to use for model registration.

    Args:
        artifacts: List of artifacts
    Returns:
        str: Selected artifact path
    """
    # Filter only directories
    dirs = [art for art in artifacts if art.is_dir]

    if not dirs:
        raise Exception("No directories found in artifacts")

    if len(dirs) == 1:
        return dirs[0].path

    print("\nMultiple model directories found. Please select one:")
    for idx, dir_artifact in enumerate(dirs, 1):
        print(f"{idx}. {dir_artifact.path}")

    while True:
        try:
            choice = int(input("\nEnter the number of your choice: "))
            if 1 <= choice <= len(dirs):
                return dirs[choice - 1].path
            print(f"Please enter a number between 1 and {len(dirs)}")
        except ValueError:
            print("Please enter a valid number")


def get_model_uri(tracking_uri, experiment_name, run_id=None):
    """
    Get model URI either from a specific run_id or the latest successful run in an experiment.
    """
    mlflow.set_tracking_uri(tracking_uri)
    print(f"Using tracking URI: {tracking_uri}")

    # Get experiment
    experiment = mlflow.get_experiment_by_name(experiment_name)
    if experiment is None:
        experiments = mlflow.search_experiments()
        available_experiments = [exp.name for exp in experiments]
        raise Exception(
            f"Experiment '{experiment_name}' not found. Available experiments: {available_experiments}"
        )

    if run_id:
        print(f"Loading model from run ID: {run_id}")
    else:
        print(f"Loading latest successful model from experiment: {experiment_name}")
        runs = mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string="status = 'FINISHED'",
            order_by=["start_time DESC"],
            max_results=1,
        )
        if runs.empty:
            raise Exception(
                f"No successful runs found in experiment '{experiment_name}'"
            )
        run_id = runs.iloc[0].run_id
        print(f"Found latest run ID: {run_id}")

    # Get run information and artifacts
    client = mlflow.tracking.MlflowClient()
    artifacts = display_artifacts(client, run_id)

    # Select model path
    model_path = select_model_path(artifacts)
    model_uri = f"runs:/{run_id}/{model_path}"
    return model_uri, run_id


def register_model(run_id, model_name):
    try:
        # Set tracking URI
        tracking_uri = os.environ.get(
            "MLFLOW_TRACKING_URI", "http://mlflow-tracking:5000"
        )
        mlflow.set_tracking_uri(tracking_uri)
        print(f"Using tracking URI: {tracking_uri}")

        # Get the run
        run = mlflow.get_run(run_id)
        if not run:
            raise Exception(f"Run {run_id} not found")

        # Register the model
        model_uri = f"runs:/{run_id}/{model_name}"
        result = mlflow.register_model(model_uri, model_name)
        print("\nModel registered successfully:")
        print(f"Name: {result.name}")
        print(f"Version: {result.version}")
        print(f"Status: {result.status}")

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def manage_tags(model_name, version=None):
    """
    Interactively manage tags for a registered model or specific version
    """
    client = mlflow.tracking.MlflowClient()

    while True:
        print("\nTag Management Options:")
        print("1. Add/Update tag")
        print("2. Delete tag")
        print("3. List current tags")
        print("4. Exit tag management")

        choice = input("\nEnter your choice (1-4): ")

        try:
            if choice == "1":
                key = input("Enter tag key: ")
                value = input("Enter tag value: ")
                if version:
                    client.set_model_version_tag(model_name, version, key, value)
                else:
                    client.set_registered_model_tag(model_name, key, value)
                print(f"Tag {key}={value} set successfully")

            elif choice == "2":
                key = input("Enter tag key to delete: ")
                if version:
                    client.delete_model_version_tag(model_name, version, key)
                else:
                    client.delete_registered_model_tag(model_name, key)
                print(f"Tag {key} deleted successfully")

            elif choice == "3":
                if version:
                    model_version = client.get_model_version(model_name, version)
                    tags = model_version.tags
                else:
                    model = client.get_registered_model(model_name)
                    tags = model.tags
                print("\nCurrent tags:")
                for key, value in tags.items():
                    print(f"{key}: {value}")

            elif choice == "4":
                break

            else:
                print("Invalid choice, please try again")

        except Exception as e:
            print(f"Error: {str(e)}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python register_model.py RUN_ID MODEL_NAME")
        sys.exit(1)

    run_id = sys.argv[1]
    model_name = sys.argv[2]
    register_model(run_id, model_name)


if __name__ == "__main__":
    main()
