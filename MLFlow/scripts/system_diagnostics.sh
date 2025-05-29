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
