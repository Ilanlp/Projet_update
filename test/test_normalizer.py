import subprocess
from pathlib import Path
import pandas as pd
from datetime import datetime
import gzip
import glob

def test_normalizer_output_columns():
    # 1. Lancer le script normalizer.py
    result = subprocess.run(
        ["python", "../pipeline/src/normalizer.py"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Erreur dans le script: {result.stderr}"

    # 2. Déterminer la date du jour
    date_str = datetime.now().strftime("%Y%m%d")

    # 3. Trouver le fichier correspondant dans pipeline/src/data/
    output_dir = Path("../pipeline/src/data")
    files = list(output_dir.glob(f"all_jobs_{date_str}_*.csv.gz"))
    assert files, f"Aucun fichier all_jobs trouvé pour la date {date_str}"

    # 4. Charger le fichier CSV.gz dans un DataFrame
    df = pd.read_csv(files[-1], compression='gzip')  # Prend le dernier fichier si plusieurs

    # 5. Vérifier qu'il y a exactement 28 colonnes
    expected_columns = 28
    actual_columns = df.shape[1]
    assert actual_columns == expected_columns, f"Le fichier {files[-1].name} contient {actual_columns} colonnes au lieu de {expected_columns}"
