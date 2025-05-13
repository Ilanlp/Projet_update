# register_pyfunc.py

from mlflow.tracking import MlflowClient

# 1) Paramètres à modifier
run_id     = "c73348e35c3047c194fc2052d06b47b5"                    # ex. "abcdef123456..."
model_uri  = f"runs:/{run_id}/matching_service"      # l'artefact que vous avez loggé
model_name = "BERT_SW_8"                  # nom que vous donnez au modèle

# 2) Création du client
client = MlflowClient()

# 3) Créer le registre (si pas déjà fait)
try:
    client.create_registered_model(model_name)
    print(f"Registered model '{model_name}'.")
except Exception:
    print(f"Model '{model_name}' already exists.")

# 4) Créer une nouvelle version
mv = client.create_model_version(
    name=model_name,
    source=model_uri,
    run_id=run_id
)
print(f"Created version {mv.version} of '{model_name}'.")

# 5) Promouvoir en Production
client.transition_model_version_stage(
    name=model_name,
    version=mv.version,
    stage="Production",
    archive_existing_versions=True
)
print(f"Transitioned '{model_name}' v{mv.version} to Production.")
