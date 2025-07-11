#!/bin/bash

# Mantra Finance Database Exporter Runner
set -e

echo "🔥 Mantra Finance Database Exporter"
echo "=================================="

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    echo "Please install uv first: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Check if service account path is set
if [ -z "$FIREBASE_SERVICE_ACCOUNT_PATH" ]; then
    echo "❌ Error: FIREBASE_SERVICE_ACCOUNT_PATH environment variable not set"
    echo ""
    echo "Please set it to your Firebase service account JSON file:"
    echo "export FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/service-account.json"
    echo ""
    echo "Or create a .env file with the path"
    exit 1
fi

# Run the exporter with uv
echo "🚀 Starting database export..."
uv run export.py

echo "✅ Export completed!"
