#!/bin/bash

# Mantra Finance Database Importer Runner
set -e

echo "📥 Mantra Finance Database Importer"
echo "==================================="

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

# Check if project ID is set
if [ -z "$FIREBASE_PROJECT_ID" ]; then
    echo "❌ Error: FIREBASE_PROJECT_ID environment variable not set"
    echo ""
    echo "Please set it to your target Firebase project ID:"
    echo "export FIREBASE_PROJECT_ID=your-project-id"
    echo ""
    echo "Or create a .env file with the project ID"
    exit 1
fi

# Safety check: Ensure service account is not prod.json
SERVICE_ACCOUNT_FILE=$(basename "$FIREBASE_SERVICE_ACCOUNT_PATH")
if [ "$SERVICE_ACCOUNT_FILE" = "prod.json" ]; then
    echo "🚨 SAFETY CHECK FAILED!"
    echo "❌ Cannot use 'prod.json' service account for imports!"
    echo ""
    echo "This is a safety measure to prevent accidental modifications to production."
    echo "Please use a different service account file (e.g., staging.json, dev.json)."
    echo ""
    echo "Current service account: $FIREBASE_SERVICE_ACCOUNT_PATH"
    exit 1
fi

# Check if service account file exists
if [ ! -f "$FIREBASE_SERVICE_ACCOUNT_PATH" ]; then
    echo "❌ Error: Service account file not found: $FIREBASE_SERVICE_ACCOUNT_PATH"
    exit 1
fi

# Check if firestore_import directory exists
IMPORT_DIR="${IMPORT_DIR:-firestore_import}"
if [ ! -d "$IMPORT_DIR" ]; then
    echo "❌ Error: Import directory not found: $IMPORT_DIR"
    echo ""
    echo "Please ensure the '$IMPORT_DIR' directory exists and contains JSON files to import."
    echo "You can set a different directory with: export IMPORT_DIR=/path/to/import/dir"
    exit 1
fi

# Check if there are JSON files to import
JSON_FILES=$(find "$IMPORT_DIR" -name "*.json" -not -name "complete_database_structure.json" | wc -l)
if [ "$JSON_FILES" -eq 0 ]; then
    echo "❌ Error: No JSON collection files found in $IMPORT_DIR/"
    echo ""
    echo "Please ensure you have collection JSON files (e.g., users.json, admins.json) in the import directory."
    echo "Note: complete_database_structure.json is ignored as it's not a collection file."
    exit 1
fi

echo "✅ Pre-flight checks passed:"
echo "   📁 Import directory: $IMPORT_DIR ($JSON_FILES collection files found)"
echo "   🔑 Service account: $SERVICE_ACCOUNT_FILE"
echo "   🎯 Target project: $FIREBASE_PROJECT_ID"

# Show database name if set
if [ -n "${FIREBASE_DATABASE_NAME:-}" ] && [ "${FIREBASE_DATABASE_NAME}" != "(default)" ]; then
    echo "   🗃️  Target database: $FIREBASE_DATABASE_NAME"
fi

# Check for dry-run mode
if [ "${DRY_RUN:-false}" = "true" ]; then
    echo "   🔍 Mode: DRY-RUN (no changes will be made)"
else
    echo "   ⚡ Mode: LIVE IMPORT"
fi

echo ""

# Run the importer with uv
echo "🚀 Starting database import..."
uv run import.py

echo "✅ Import process completed!"
