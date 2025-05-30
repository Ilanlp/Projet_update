import mlflow
import sys


def list_runs():
    # Set tracking URI
    mlflow.set_tracking_uri("http://mlflow-tracking:5000")

    # Get all experiments
    experiments = mlflow.search_experiments()

    print("\nAvailable experiments:")
    for exp in experiments:
        print(f"\nExperiment: {exp.name} (ID: {exp.experiment_id})")

        # Get runs for this experiment
        runs = mlflow.search_runs(experiment_ids=[exp.experiment_id])

        if len(runs) > 0:
            print("\nRuns:")
            for _, run in runs.iterrows():
                print(f"  Run ID: {run.run_id}")
                print(f"  Status: {run.status}")
                print(f"  Start time: {run.start_time}")
                if "metrics.test_rmse" in run:
                    print(f"  Test RMSE: {run['metrics.test_rmse']:.2f}")
                print("")
        else:
            print("No runs found")


if __name__ == "__main__":
    try:
        list_runs()
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
