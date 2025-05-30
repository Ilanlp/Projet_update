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
