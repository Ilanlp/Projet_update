#!/bin/bash
set -e

# Fonction pour vérifier l'utilisateur actuel
check_current_user() {
    local target_user="$1"
    local current_user=$(whoami)
    
    if [ "$current_user" = "$target_user" ]; then
        echo "✅ Déjà en tant qu'utilisateur $target_user"
        return 0
    else
        echo "ℹ️ Changement vers l'utilisateur $target_user nécessaire"
        return 1
    fi
}

# Fonction pour vérifier si nous sommes dans WSL
is_wsl() {
    if [ -f /proc/version ]; then
        if grep -qi microsoft /proc/version; then
            return 0
        fi
    fi
    return 1
}

# Fonction pour configurer les permissions avec timeout
configure_path_permissions() {
    local path="$1"
    local is_system_path="$2"
    local timeout_duration=5

    if [ ! -d "$path" ]; then
        echo "📁 Création du répertoire $path"
        mkdir -p "$path" || true
    fi

    echo "🔧 Configuration des permissions pour $path"
    
    # Pour les chemins système, on vérifie juste l'accès
    if [ "$is_system_path" = "true" ]; then
        if su - mlflow -c "test -r '$path' && test -x '$path'" 2>/dev/null; then
            echo "✅ $path est accessible en lecture/exécution"
            return 0
        else
            echo "⚠️ $path n'est pas accessible - vérifiez les permissions système"
            return 1
        fi
    fi

    # Pour les chemins d'application, on essaie de modifier les permissions
    if timeout ${timeout_duration}s bash -c "chown -R mlflow:mlflow '$path' 2>/dev/null && chmod -R 755 '$path' 2>/dev/null"; then
        echo "✅ Permissions configurées pour $path"
        return 0
    else
        echo "⚠️ Impossible de configurer toutes les permissions pour $path"
        # Vérifie au moins l'accès
        if su - mlflow -c "test -r '$path' && test -x '$path'" 2>/dev/null; then
            echo "✅ Mais $path reste accessible en lecture/exécution"
            return 0
        fi
        return 1
    fi
}

echo "ℹ️ [$(date +"%Y-%m-%d %H:%M:%S")] Démarrage de la configuration..."

# Détection de l'environnement
if is_wsl; then
    echo "🔍 Environnement WSL détecté - adaptation des permissions..."
fi

# Chemins d'application (peuvent être modifiés)
APP_PATHS=(
    "/app/models"
    "/app/logs"
    "/app/data"
    "/app/config"
    "/app/cache"
    "/app/experiments"
    "/app/temp"
    "/app/mlruns"
)

# Chemins système (lecture seule suffisante)
SYSTEM_PATHS=(
    "/opt/venv"
)

# Configuration des chemins d'application
for path in "${APP_PATHS[@]}"; do
    configure_path_permissions "$path" false
done

# Configuration des chemins système
for path in "${SYSTEM_PATHS[@]}"; do
    configure_path_permissions "$path" true
done

# Activation de l'environnement virtuel
if [ -f /opt/venv/bin/activate ]; then
    echo "🐍 Activation de l'environnement virtuel..."
    . /opt/venv/bin/activate
fi

echo "🚀 Démarrage de l'application..."

# Vérification et switch utilisateur intelligent
if check_current_user "mlflow"; then
    exec "$@"
else
    exec gosu mlflow "$@"
fi
