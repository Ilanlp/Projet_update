#!/bin/bash

# ===========================================
# ml_entrypoint.sh - Script d'initialisation ML
# ===========================================

set -e

# Fonctions de logging avec couleurs
log_info() {
  echo -e "\033[0;34mℹ️  [$(date '+%Y-%m-%d %H:%M:%S')]\033[0m $1"
}

log_success() {
  echo -e "\033[0;32m✅ [$(date '+%Y-%m-%d %H:%M:%S')]\033[0m $1"
}

log_warning() {
  echo -e "\033[0;33m⚠️  [$(date '+%Y-%m-%d %H:%M:%S')]\033[0m $1"
}

log_error() {
  echo -e "\033[0;31m❌ [$(date '+%Y-%m-%d %H:%M:%S')]\033[0m $1"
}

# Configuration des répertoires
setup_directories() {
  log_info "Setting up working directories..."

  # Création des répertoires principaux
  mkdir -p /app/{data,models,logs,cache,experiments,temp,config,scripts}
  mkdir -p /app/cache/{matplotlib,transformers,huggingface,sklearn}
  mkdir -p /tmp/mlflow

  # Permissions
  chmod 755 /app/{data,models,logs,config,scripts}
  chmod 777 /app/{cache,temp} /tmp/mlflow

  log_success "Working directories created"
}

# Configuration de l'environnement Python
setup_python_environment() {
  log_info "Configuring Python environment..."

  # Variables d'environnement Python
  export PYTHONPATH="/app:/app/src:$PYTHONPATH"
  export PYTHONUNBUFFERED=1
  export PYTHONDONTWRITEBYTECODE=1

  # Configuration des caches
  export MPLCONFIGDIR=/app/cache/matplotlib
  export TRANSFORMERS_CACHE=/app/cache/transformers
  export HF_HOME=/app/cache/huggingface
  export SKLEARN_CACHE_DIR=/app/cache/sklearn
  export TMPDIR=/app/temp

  log_success "Python environment configured"
}

# Configuration MLflow
setup_mlflow() {
  log_info "Configuring MLflow..."

  # Variables d'environnement MLflow
  export MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI:-"http://mlflow-tracking:5000"}
  export MLFLOW_ARTIFACT_ROOT=${MLFLOW_ARTIFACT_ROOT:-"/app/mlruns"}
  export MLFLOW_EXPERIMENT_NAME=${MLFLOW_EXPERIMENT_NAME:-"default"}

  log_success "MLflow configured"
}

# Configuration du logging
setup_logging() {
  log_info "Setting up logging..."

  # Création des fichiers de log
  touch /app/logs/training.log /app/logs/errors.log

  # Niveau de log
  export TRAINING_LOG_LEVEL=${TRAINING_LOG_LEVEL:-"INFO"}

  log_success "Logging system configured"
}

# Configuration du shell et des aliases
setup_shell_environment() {
  log_info "Setting up shell environment..."

  # Création du fichier de configuration bash
  cat >~/.bashrc <<'EOF'
# ===========================================
# ML Training Container - Custom Configuration
# ===========================================

# Fonctions de logging avec couleurs
log_info() {
  echo -e "\033[0;34mℹ️  [$(date '+%Y-%m-%d %H:%M:%S')]\033[0m $1"
}

log_success() {
  echo -e "\033[0;32m✅ [$(date '+%Y-%m-%d %H:%M:%S')]\033[0m $1"
}

log_warning() {
  echo -e "\033[0;33m⚠️  [$(date '+%Y-%m-%d %H:%M:%S')]\033[0m $1"
}

log_error() {
  echo -e "\033[0;31m❌ [$(date '+%Y-%m-%d %H:%M:%S')]\033[0m $1"
}

# Prompt personnalisé
export PS1="🤖 [\[\033[1;34m\]ML-Training\[\033[0m\]] \[\033[1;32m\]\w\[\033[0m\] $ "

# Aliases de base
alias ll='ls -la'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'

# Aliases ML spécifiques
alias train='python /app/src/train_model.py'
alias register='python /app/src/register_model.py'
alias serve='python /app/src/serve_model.py'
alias test='python /app/src/test_model.py'
alias logs='tail -f /app/logs/training.log'
alias errorlogs='tail -f /app/logs/errors.log'

# Aliases MLflow
alias mlflow-ui='mlflow ui --host 0.0.0.0 --port 5001'
alias mlflow-experiments='python -c "import mlflow; [print(f\"{e.name}: {e.experiment_id}\") for e in mlflow.search_experiments()]"'
alias mlflow-models='python -c "import mlflow; [print(f\"{m.name}\") for m in mlflow.MlflowClient().search_registered_models()]"'

# Fonctions utiles
quick_train() {
  echo "🚀 Starting quick training..."
  python /app/src/train_model.py --n-samples 1000 --no-hyperparameter-tuning
}

full_train() {
  echo "🎯 Starting full training with optimization..."
  python /app/src/train_model.py --n-samples 5000 --feature-engineering
}

mlflow_status() {
  echo "📊 MLflow Status:"
  echo "   URI: ${MLFLOW_TRACKING_URI}"
  if curl -s "${MLFLOW_TRACKING_URI}/health" > /dev/null; then
    echo "   Status: ✅ Online"
  else
    echo "   Status: ❌ Offline"
  fi
}

show_model_info() {
  local model_name=$1
  if [ -z "$model_name" ]; then
    echo "Usage: show_model_info MODEL_NAME"
    return 1
  fi
  
  echo "ℹ️  Fetching model information..."
  python /app/src/show_model_info.py "$model_name"
}

# Message de bienvenue
echo ""
echo "🎯 ML Training Environment Ready!"
echo "Available commands:"
echo "  - quick_train    : Run quick training with reduced dataset"
echo "  - full_train     : Run full training with optimization"
echo "  - mlflow_status  : Check MLflow server status"
echo "  - show_model_info MODEL_NAME : Show detailed model information"
echo ""
EOF

  # Sourcer le fichier bashrc
  source ~/.bashrc

  log_success "Shell environment configured"
}

# Affichage des informations système
show_system_information() {
  log_info "System Information:"
  echo "🖥️  Container: ML Training Service"
  echo "🐍 Python: $(python --version 2>&1)"
  echo "🧠 CPU Cores: $(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 'N/A')"

  # Détection cross-platform de la mémoire
  if [ "$(uname)" == "Darwin" ]; then
    # macOS
    echo "💾 Memory: $(sysctl -n hw.memsize 2>/dev/null | awk '{ printf "%.2fGB\n", $1/1024/1024/1024 }' || echo 'N/A')"
  else
    # Linux
    echo "💾 Memory: $(free -h 2>/dev/null | awk '/^Mem:/ {print $2}' || echo 'N/A')"
  fi

  echo "💿 Disk Space: $(df -h /app | awk 'NR==2 {print $4}' 2>/dev/null || echo 'N/A')"
  echo "👤 User: $(whoami)"
  echo "📁 Working Dir: $(pwd)"
  echo "🌐 MLflow URI: ${MLFLOW_TRACKING_URI}"
  echo ""
  echo "📋 Available Commands:"
  echo "   🚀 train                    # Train a new model"
  echo "   📊 list-runs                # List all MLflow runs"
  echo "   💾 register RUN_ID MODEL    # Register a model in MLflow"
  echo "   🌐 serve --port PORT        # Serve model (default: 5001)"
  echo "   🧪 test                     # Run model tests"
  echo "   📝 logs                     # View training logs"
  echo "   ❌ errorlogs                # View error logs"
  echo "   ℹ️  help                     # Show help message"
  echo ""
  echo "📋 Quick Commands:"
  echo "   🚀 quick_train              # Train with small dataset"
  echo "   🎯 full_train               # Train with full optimization"
  echo "   📊 mlflow_status            # Check MLflow server status"
  echo "   ℹ️  show_model_info NAME     # Show model details"
  echo ""
}

# Nettoyage
cleanup() {
  log_info "Performing cleanup..."

  # Nettoyage des fichiers temporaires
  rm -rf /tmp/mlflow/* 2>/dev/null || true
  rm -rf /app/temp/* 2>/dev/null || true

  log_success "Cleanup completed"
}

# Fonction pour exécuter train_model.py
run_training() {
  log_info "Starting model training..."
  python /app/src/train_model.py
  log_success "Training completed"
}

# Fonction pour exécuter register_model.py
run_registration() {
  local run_id=$1
  local model_name=$2

  if [ -z "$run_id" ] || [ -z "$model_name" ]; then
    log_error "Usage: register_model RUN_ID MODEL_NAME"
    return 1
  fi

  log_info "Registering model..."
  python /app/src/register_model.py "$run_id" "$model_name"
  log_success "Model registration completed"
}

# Fonction pour exécuter serve_model.py
run_serving() {
  local tracking_uri=${MLFLOW_TRACKING_URI:-"http://mlflow-tracking:5000"}
  local port=${1:-5001}

  log_info "Starting model serving..."
  python /app/src/serve_model.py --tracking_uri "$tracking_uri" --port "$port"
}

# Fonction pour exécuter test_model.py
run_testing() {
  log_info "Starting model testing..."
  python /app/src/test_model.py
  log_success "Testing completed"
}

# Fonction d'aide
show_help() {
  echo "Usage: $0 COMMAND [args...]"
  echo ""
  echo "MLflow Training Container - Available Commands:"
  echo ""
  echo "Model Management:"
  echo "  train                          Train a new model using train_model.py"
  echo "  register RUN_ID MODEL_NAME     Register a trained model in MLflow registry"
  echo "  serve [--port PORT]            Serve a model (default port: 5001)"
  echo "  test                           Run model tests and validation"
  echo ""
  echo "MLflow Operations:"
  echo "  list-runs                      List all experiments and their runs"
  echo "  setup                          Setup environment only"
  echo "  help                           Show this help message"
  echo ""
  echo "Shell Access:"
  echo "  bash                           Start an interactive bash shell"
  echo "  sh                             Start an interactive sh shell"
  echo ""
  echo "Environment Variables:"
  echo "  MLFLOW_TRACKING_URI            MLflow tracking server URI"
  echo "  MLFLOW_EXPERIMENT_NAME         MLflow experiment name"
  echo "  MLFLOW_ARTIFACT_ROOT           MLflow artifact root directory"
  echo "  MODEL_URI                      URI of the model to serve"
  echo "  TRAINING_LOG_LEVEL             Logging level for training"
  echo ""
  echo "Examples:"
  echo "  $0 train                       # Train a new model"
  echo "  $0 register abc123 MyModel     # Register run abc123 as MyModel"
  echo "  $0 serve --port 5001           # Serve model on port 5001"
  echo "  $0 list-runs                   # List all MLflow runs"
}

# Test de la configuration complète
test_training_environment() {
  log_info "Testing training environment..."

  # Test des imports
  python -c "
import mlflow, sklearn, pandas, numpy
print('✅ Core packages imported successfully')
" || {
    log_error "Package import test failed"
    exit 1
  }

  # Test de la connectivité MLflow
  if curl -s --max-time 5 "${MLFLOW_TRACKING_URI}/health" >/dev/null; then
    log_success "MLflow connectivity test passed"
  else
    log_warning "MLflow connectivity test failed"
  fi

  # Test des scripts
  # if [ -x "/app/scripts/model_validation.py" ] && [ -x "/app/scripts/hyperparameter_optimization.py" ]; then
  #   log_success "Training scripts are executable"
  # else
  #   log_error "Training scripts test failed"
  #   exit 1
  # fi

  log_success "Environment tests completed"
}

# Fonction principale
main() {
  # Configuration initiale de l'environnement
  setup_directories
  setup_python_environment
  setup_mlflow
  setup_logging
  setup_shell_environment

  # Informations système
  show_system_information

  # Si aucun argument n'est fourni, afficher l'aide
  if [ $# -eq 0 ]; then
    show_help
    exit 0
  fi

  # Traitement des commandes shell directes
  if [[ "$1" == "bash" ]] || [[ "$1" == "sh" ]]; then
    exec "$1"
    return
  fi

  # Traitement des commandes spécifiques
  case "$1" in
  train)
    shift
    log_info "Starting model training..."
    python /app/src/train_model.py "$@"
    ;;
  register)
    shift
    if [ $# -lt 2 ]; then
      log_error "Usage: register RUN_ID MODEL_NAME"
      exit 1
    fi
    log_info "Registering model..."
    python /app/src/register_model.py "$@"
    ;;
  serve)
    shift
    log_info "Starting model serving..."
    python /app/src/serve_model.py "$@"
    ;;
  test)
    shift
    log_info "Running model tests..."
    python /app/src/test_model.py "$@"
    ;;
  list-runs)
    shift
    log_info "Listing MLflow runs..."
    python /app/src/list_runs.py "$@"
    ;;
  setup)
    log_success "Environment setup completed"
    ;;
  help)
    show_help
    ;;
  *)
    log_error "Unknown command: $1"
    show_help
    exit 1
    ;;
  esac

  log_success "🎉 Command executed successfully!"
}

# Gestion des signaux pour arrêt propre
trap 'log_info "Received shutdown signal"; cleanup; exit 0' SIGTERM SIGINT

# Si le script est exécuté directement
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
