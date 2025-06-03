#!/bin/bash
# Script de rotation des logs
LOG_DIR="/app/logs"
MAX_SIZE="100M"
MAX_FILES=5

for log_file in "${LOG_DIR}"/*.log; do
    if [ -f "$log_file" ] && [ $(stat -f%z "$log_file" 2>/dev/null || stat -c%s "$log_file" 2>/dev/null) -gt $((100 * 1024 * 1024)) ]; then
        mv "$log_file" "${log_file}.$(date +%Y%m%d_%H%M%S)"
        touch "$log_file"

        # Garder seulement les derniers fichiers
        ls -t "${log_file}".* | tail -n +$((MAX_FILES + 1)) | xargs -r rm
    fi
done
