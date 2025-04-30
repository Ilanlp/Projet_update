import os
import argparse
from pathlib import Path


def analyze_path(path):
    """
    Analyse et retourne des informations sur le chemin fourni.

    Args:
        path (str): Le chemin à analyser.

    Returns:
        dict: Un dictionnaire contenant les informations sur le chemin.
    """
    # Convertir en chemin absolu et normaliser
    try:
        # Convertir le chemin relatif en absolu
        abs_path = os.path.abspath(path)

        # Normaliser le chemin (résoudre les '.', '..')
        norm_path = os.path.normpath(abs_path)

        # Vérifier si le chemin existe
        exists = os.path.exists(norm_path)

        # Déterminer si c'est un fichier ou un répertoire
        is_file = os.path.isfile(norm_path) if exists else None
        is_dir = os.path.isdir(norm_path) if exists else None

        # Obtenir le répertoire parent
        parent = os.path.dirname(norm_path)

        # Obtenir les composants du chemin
        parts = Path(norm_path).parts

        # Obtenir les permissions si le chemin existe
        if exists:
            stats = os.stat(norm_path)
            permissions = oct(stats.st_mode)[-3:]
        else:
            permissions = None

        return {
            "original_path": path,
            "absolute_path": abs_path,
            "normalized_path": norm_path,
            "exists": exists,
            "is_file": is_file,
            "is_directory": is_dir,
            "parent_directory": parent,
            "path_components": parts,
            "permissions": permissions,
        }

    except Exception as e:
        return {"original_path": path, "error": str(e)}


def main():
    # Configurer le parseur d'arguments
    parser = argparse.ArgumentParser(description="Analyser un chemin fourni.")
    parser.add_argument("path", type=str, help="Le chemin à analyser")

    # Parser les arguments
    args = parser.parse_args()

    # Analyser le chemin
    result = analyze_path(args.path)

    # Afficher les résultats
    print("\n=== Analyse du chemin ===")
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
