#!/bin/bash
set -e

# Activation de l'environnement virtuel
source /opt/venv/bin/activate

# Exécution de la commande passée en argument
exec "$@"
