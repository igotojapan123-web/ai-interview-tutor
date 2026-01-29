#!/bin/bash
# healthcheck.sh
# FlyReady Lab - Health Check Script

set -e

# Check Streamlit
if ! curl -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    echo "Streamlit health check failed"
    exit 1
fi

# Check API (if running)
if [ -n "$API_PORT" ]; then
    if ! curl -f http://localhost:${API_PORT}/health > /dev/null 2>&1; then
        echo "API health check failed"
        exit 1
    fi
fi

echo "Health check passed"
exit 0
