#!/bin/bash

# ===========================================
# training_entrypoint.sh - Script d'initialisation Training
# Chemin: scripts/training_entrypoint.sh
# ===========================================

set -e

echo "🤖 Starting ML Training Container Setup..."

# Variables d'environnement par défaut
MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI:-http://mlflow-tracking:5000}
MLFLOW_ARTIFACT_ROOT=${MLFLOW_ARTIFACT_ROOT:-/app/mlruns}
MLFLOW_EXPERIMENT_NAME=${MLFLOW_EXPERIMENT_NAME:-default}
TRAINING_LOG_LEVEL=${LOG_LEVEL:-INFO}

# Fonction de logging avec couleurs
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

# Vérification de la connectivité MLflow
check_mlflow_connection() {
  log_info "Checking MLflow connection..."
  local max_attempts=30
  local attempt=1

  while [ $attempt -le $max_attempts ]; do
    if curl -s --max-time 5 "${MLFLOW_TRACKING_URI}/health" >/dev/null 2>&1; then
      log_success "MLflow server is accessible at ${MLFLOW_TRACKING_URI}"
      return 0
    fi

    log_info "Waiting for MLflow server... (attempt $attempt/$max_attempts)"
    sleep 2
    ((attempt++))
  done

  log_warning "MLflow server not accessible after $((max_attempts * 2)) seconds"
  log_warning "Training will continue but MLflow features may not work"
  return 1
}

# Configuration des répertoires de travail
setup_directories() {
  log_info "Setting up working directories..."

  # Créer les répertoires nécessaires
  mkdir -p /app/{data,models,experiments,logs,cache,temp,config,scripts}
  mkdir -p /app/cache/{matplotlib,transformers,huggingface,sklearn}
  mkdir -p /tmp/mlflow

  # Permissions appropriées
  chmod 755 /app/{data,models,experiments,logs,config,scripts}
  chmod 777 /app/{cache,temp} /tmp/mlflow

  # Créer des sous-répertoires organisés
  mkdir -p /app/models/{trained,exported,archived}
  mkdir -p /app/experiments/{configs,results,reports}
  mkdir -p /app/logs/{training,validation,errors}

  log_success "Working directories created"
}

# Configuration de l'environnement Python
setup_python_environment() {
  log_info "Configuring Python environment..."

  # Validation des packages critiques
  local packages=("mlflow" "sklearn" "pandas" "numpy" "matplotlib" "seaborn")
  for package in "${packages[@]}"; do
    if python -c "import $package; print(f'✅ $package {$package.__version__}')" 2>/dev/null; then
      log_success "$package is available"
    else
      log_error "$package is not available"
      exit 1
    fi
  done

  # Configuration matplotlib pour mode headless
  mkdir -p ~/.matplotlib
  echo "backend: Agg" >~/.matplotlib/matplotlibrc

  # Configuration des variables d'environnement Python
  export PYTHONPATH="/app:/app/src:$PYTHONPATH"
  export PYTHONUNBUFFERED=1
  export PYTHONDONTWRITEBYTECODE=1
  export PYTHONHASHSEED=0

  log_success "Python environment configured"
}

# Configuration MLflow
setup_mlflow_environment() {
  log_info "Configuring MLflow environment..."

  # Vérifier la connectivité
  local mlflow_available=false
  if check_mlflow_connection; then
    mlflow_available=true
  fi

  # Configuration des variables MLflow
  export MLFLOW_TRACKING_URI="${MLFLOW_TRACKING_URI}"
  export MLFLOW_ARTIFACT_ROOT="${MLFLOW_ARTIFACT_ROOT}"
  export MLFLOW_EXPERIMENT_NAME="${MLFLOW_EXPERIMENT_NAME}"
  export MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING=true

  # Test de la configuration MLflow
  if [ "$mlflow_available" = true ]; then
    python -c "
import mlflow
mlflow.set_tracking_uri('${MLFLOW_TRACKING_URI}')
try:
    experiments = mlflow.search_experiments()
    print(f'✅ MLflow connected: {len(experiments)} experiments found')
except Exception as e:
    print(f'⚠️ MLflow connection issue: {e}')
" 2>/dev/null || log_warning "MLflow test failed"
  fi

  log_info "MLflow configuration:"
  echo "   📊 Tracking URI: ${MLFLOW_TRACKING_URI}"
  echo "   📁 Artifact Root: ${MLFLOW_ARTIFACT_ROOT}"
  echo "   🧪 Experiment: ${MLFLOW_EXPERIMENT_NAME}"
  echo "   📈 System Metrics: Enabled"
}

# Configuration du logging
setup_logging_system() {
  log_info "Setting up logging system..."

  # Configuration du logging Python
  cat >/app/config/logging.conf <<'EOF'
[loggers]
keys=root,training,mlflow

[handlers]
keys=consoleHandler,fileHandler,errorHandler

[formatters]
keys=detailedFormatter,simpleFormatter

[logger_root]
level=INFO
handlers=consoleHandler

[logger_training]
level=DEBUG
handlers=consoleHandler,fileHandler
qualname=training
propagate=0

[logger_mlflow]
level=INFO
handlers=consoleHandler,fileHandler
qualname=mlflow
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=DEBUG
formatter=detailedFormatter
args=('/app/logs/training.log', 'a')

[handler_errorHandler]
class=FileHandler
level=ERROR
formatter=detailedFormatter
args=('/app/logs/errors.log', 'a')

[formatter_simpleFormatter]
format=[%(levelname)s] %(message)s

[formatter_detailedFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s
datefmt=%Y-%m-%d %H:%M:%S
EOF

  # Créer les fichiers de log
  touch /app/logs/training.log /app/logs/errors.log

  # Script de rotation des logs
  cat >/app/scripts/rotate_logs.sh <<'EOF'
#!/bin/bash
# Script de rotation des logs
LOG_DIR="/app/logs"
MAX_SIZE="100M"
MAX_FILES=5

for log_file in "${LOG_DIR}"/*.log; do
    if [ -f "$log_file" ] && [ $(stat -f%z "$log_file" 2>/dev/null || stat -c%s "$log_file" 2>/dev/null) -gt $((100*1024*1024)) ]; then
        mv "$log_file" "${log_file}.$(date +%Y%m%d_%H%M%S)"
        touch "$log_file"
        
        # Garder seulement les derniers fichiers
        ls -t "${log_file}".* | tail -n +$((MAX_FILES+1)) | xargs -r rm
    fi
done
EOF
  chmod +x /app/scripts/rotate_logs.sh

  log_success "Logging system configured"
}

# Configuration des optimisations système
setup_system_optimizations() {
  log_info "Applying system optimizations..."

  # Optimisations CPU
  export OMP_NUM_THREADS=${OMP_NUM_THREADS:-4}
  export OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-4}
  export MKL_NUM_THREADS=${MKL_NUM_THREADS:-4}
  export NUMBA_NUM_THREADS=${NUMBA_NUM_THREADS:-4}

  # Optimisations mémoire
  export JOBLIB_TEMP_FOLDER=/tmp
  export TMPDIR=/app/temp

  # Configuration des caches
  export MPLCONFIGDIR=/app/cache/matplotlib
  export TRANSFORMERS_CACHE=/app/cache/transformers
  export HF_HOME=/app/cache/huggingface
  export SKLEARN_CACHE_DIR=/app/cache/sklearn

  log_info "System optimizations applied:"
  echo "   🧵 CPU Threads: ${OMP_NUM_THREADS}"
  echo "   💾 Temp Dir: ${TMPDIR}"
  echo "   📦 Cache Dir: /app/cache"
}

# Installation des outils de monitoring
setup_monitoring_tools() {
  log_info "Setting up monitoring tools..."

  # Script de monitoring système
  cat >/app/scripts/monitor_training.sh <<'EOF'
#!/bin/bash
# Script de monitoring pour l'entraînement

INTERVAL=${1:-10}  # Intervalle en secondes
LOG_FILE="/app/logs/system_monitor.log"

echo "$(date): Starting system monitoring (interval: ${INTERVAL}s)" >> "$LOG_FILE"

while true; do
    {
        echo "=== $(date) ==="
        echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)"
        echo "Memory Usage: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
        echo "Disk Usage: $(df /app | tail -1 | awk '{print $5}')"
        echo "Load Average: $(uptime | awk -F'load average:' '{print $2}')"
        echo "Active Python Processes: $(pgrep -c python || echo 0)"
        echo ""
    } >> "$LOG_FILE"
    
    sleep "$INTERVAL"
done
EOF
  chmod +x /app/scripts/monitor_training.sh

  # Script de diagnostic système
  cat >/app/scripts/system_diagnostics.sh <<'EOF'
#!/bin/bash
# Script de diagnostic système complet

echo "🔍 System Diagnostics Report"
echo "==============================="
echo "📅 Date: $(date)"
echo "🖥️  Hostname: $(hostname)"
echo "👤 User: $(whoami)"
echo "📁 Working Directory: $(pwd)"
echo ""

echo "🐍 Python Environment:"
echo "   Python Version: $(python --version)"
echo "   Python Path: $(which python)"
echo "   Pip Version: $(pip --version | cut -d' ' -f1-2)"
echo ""

echo "📊 System Resources:"
echo "   CPU Cores: $(nproc)"
echo "   Total Memory: $(free -h | awk '/^Mem:/ {print $2}')"
echo "   Available Memory: $(free -h | awk '/^Mem:/ {print $7}')"
echo "   Disk Space (/)): $(df -h / | awk 'NR==2 {print $4}')"
echo "   Disk Space (/app): $(df -h /app | awk 'NR==2 {print $4}' 2>/dev/null || echo 'N/A')"
echo ""

echo "🔧 Environment Variables:"
echo "   MLFLOW_TRACKING_URI: ${MLFLOW_TRACKING_URI:-'Not set'}"
echo "   PYTHONPATH: ${PYTHONPATH:-'Not set'}"
echo "   OMP_NUM_THREADS: ${OMP_NUM_THREADS:-'Not set'}"
echo "   TMPDIR: ${TMPDIR:-'Not set'}"
echo ""

echo "📦 Key Python Packages:"
python -c "
import sys
packages = ['numpy', 'pandas', 'scikit-learn', 'matplotlib', 'mlflow']
for pkg in packages:
    try:
        module = __import__(pkg.replace('-', '_'))
        version = getattr(module, '__version__', 'Unknown')
        print(f'   {pkg}: {version}')
    except ImportError:
        print(f'   {pkg}: Not installed')
"
echo ""

echo "🌐 Network Connectivity:"
if curl -s --max-time 5 "${MLFLOW_TRACKING_URI:-http://mlflow-tracking:5000}/health" > /dev/null; then
    echo "   ✅ MLflow Server: Accessible"
else
    echo "   ❌ MLflow Server: Not accessible"
fi

echo ""
echo "📁 Directory Structure:"
echo "   /app contents:"
ls -la /app/ 2>/dev/null | head -10 || echo "   Directory not accessible"

echo ""
echo "📋 Active Processes:"
ps aux | grep -E "(python|jupyter|mlflow)" | grep -v grep | head -5 || echo "   No relevant processes found"

echo ""
echo "==============================="
echo "✅ Diagnostics completed"
EOF
  chmod +x /app/scripts/system_diagnostics.sh

  log_success "Monitoring tools configured"
}

# Configuration des aliases et helpers
setup_shell_environment() {
  log_info "Setting up shell environment..."

  # Configuration bash avec des aliases utiles
  cat >>~/.bashrc <<'EOF'

# ===========================================
# ML Training Container - Custom Configuration
# ===========================================

# Prompt personnalisé
export PS1="🤖 [\[\033[1;34m\]ML-Training\[\033[0m\]] \[\033[1;32m\]\w\[\033[0m\] $ "

# Aliases utiles
alias ll='ls -la'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'

# Aliases ML spécifiques
alias train='python src/train_model.py'
alias trainreal='python src/train_model.py'
alias validate='python scripts/model_validation.py'
alias logs='tail -f /app/logs/training.log'
alias errorlogs='tail -f /app/logs/errors.log'
alias models='ls -la /app/models/'
alias experiments='ls -la /app/experiments/'
alias monitor='bash /app/scripts/monitor_training.sh'
alias diagnose='/app/scripts/system_diagnostics.sh'

# Aliases MLflow
alias mlflow-ui='mlflow ui --host 0.0.0.0 --port 5001'
alias mlflow-experiments='python -c "import mlflow; [print(f\"{e.name}: {e.experiment_id}\") for e in mlflow.search_experiments()]"'
alias mlflow-models='python -c "import mlflow; [print(f\"{m.name}\") for m in mlflow.MlflowClient().search_registered_models()]"'

# Variables d'environnement
export PYTHONPATH="/app:/app/src:$PYTHONPATH"
export EDITOR=nano
export PAGER=less

# Fonctions utiles
quick_train() {
    echo "🚀 Starting quick training..."
    python src/train_model.py --n-samples 1000 --no-hyperparameter-tuning --register
}

full_train() {
    echo "🎯 Starting full training with optimization..."
    python src/train_model.py --n-samples 5000 --feature-engineering --register --stage Production
}

check_gpu() {
    if command -v nvidia-smi &> /dev/null; then
        nvidia-smi
    else
        echo "GPU not available or nvidia-smi not installed"
    fi
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

# Auto-complétion pour nos commandes
complete -W "--help --n-samples --model-name --experiment-name --register --stage --feature-engineering" train
complete -W "--help --data-path --model-name --experiment-name --register --stage" trainreal

echo ""
echo "🎯 ML Training Environment Ready!"
echo "Type 'diagnose' for system info or 'quick_train' to start training"
echo ""
EOF

  log_success "Shell environment configured"
}

# Affichage des informations système
show_system_information() {
  log_info "System Information:"
  echo "🖥️  Container: ML Training Service"
  echo "🐍 Python: $(python --version)"
  echo "🧠 CPU Cores: $(nproc)"
  echo "💾 Memory: $(free -h | awk '/^Mem:/ {print $2}')"
  echo "💿 Disk Space: $(df -h /app | awk 'NR==2 {print $4}' 2>/dev/null || echo 'N/A')"
  echo "👤 User: $(whoami)"
  echo "📁 Working Dir: $(pwd)"
  echo "🌐 MLflow URI: ${MLFLOW_TRACKING_URI}"
  echo ""
  echo "📋 Available Commands:"
  echo "   🚀 train                    # Quick synthetic training"
  echo "   🎯 full_train              # Full training with optimization"
  echo "   ☑️  validate --model-name   # Validate a model"
  echo "   📊 diagnose               # System diagnostics"
  echo "   📈 monitor                # System monitoring"
  echo "   📝 logs                   # View training logs"
  echo ""
}

# Fonction de nettoyage à l'arrêt
cleanup() {
  log_info "Performing cleanup..."

  # Arrêter les processus de monitoring
  pkill -f monitor_training.sh 2>/dev/null || true

  # Nettoyer les fichiers temporaires
  rm -rf /tmp/mlflow/* 2>/dev/null || true
  rm -rf /app/temp/* 2>/dev/null || true

  # Rotation des logs si nécessaire
  /app/scripts/rotate_logs.sh 2>/dev/null || true

  log_success "Cleanup completed"
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
  log_info "Starting ML Training Container initialization..."

  # Setup des composants
  setup_directories
  setup_python_environment
  setup_mlflow_environment
  setup_logging_system
  setup_system_optimizations
  setup_monitoring_tools
  setup_shell_environment

  # Tests
  test_training_environment

  # Informations système
  show_system_information

  log_success "🎉 ML Training Container ready!"
  log_info "Container initialization completed successfully"

  # Exécuter la commande passée en argument
  # if [ $# -gt 0 ]; then
  #   log_info "Executing command: $*"
  #   exec "$@"
  # else
  #   log_info "No command specified, starting interactive shell"
  #   exec bash
  # fi
  log_info "No command specified, starting interactive shell"
  exec bash
}

# Gestion des signaux pour arrêt propre
trap 'log_info "Received shutdown signal"; cleanup; exit 0' SIGTERM SIGINT

# Exécution du script principal
main "$@"
