# Firestore Import Export Tool

Tools for safely exporting and importing Firebase Firestore database structure and data.

## 🎯 Purpose

These tools help you manage your Firebase databases by providing:

### Export Tool (`export.py`)
- **Read-only** database structure export
- Sample documents (configurable limit)
- Data types and relationships analysis
- JSON output for easy analysis

### Import Tool (`import.py`)
- **Safe** database import with multiple safety checks
- Interactive collection selection
- Dry-run mode for testing
- Production protection (blocks prod.json usage)

**⚠️ SAFETY FIRST**: Export tool only performs READ operations. Import tool includes multiple safety checks.

## 🚀 Setup

1. **Install dependencies using uv**:
   ```bash
   uv sync
   ```

2. **Get Firebase Service Account Key**:
   - Go to Firebase Console → Project Settings → Service Accounts
   - Generate a new private key
   - Download the JSON file
   - **IMPORTANT**: Do not name production keys `prod.json` as the import tool blocks this for safety

## 📋 Usage

### Export Database Structure

```bash
# Set your service account path
export FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/service-account.json

# Run the export
./run_export.sh
```

Custom configuration:
```bash
export FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/service-account.json
export SAMPLE_LIMIT=10
export OUTPUT_DIR=my_export
./run_export.sh
```

### Import Database Collections

```bash
# Set required environment variables
export FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/service-account.json
export FIREBASE_PROJECT_ID=your-target-project-id

# Optional: Enable dry-run mode first (recommended)
export DRY_RUN=true

# Run the import
./run_import.sh
```

## 📂 File Structure

```
utils/
├── export.py                   # Database export tool
├── import.py                   # Database import tool
├── run_export.sh               # Export runner script
├── run_import.sh               # Import runner script
├── firestore_export/           # Export output directory
├── firestore_import/           # Import input directory
├── firestore_import_reports/   # Import reports directory
└── README.md                   # This file
```

## 📊 Output Structure

### Export Output
- `firestore_export/` directory (or custom name)
- `complete_database_structure.json` - Full database overview
- Individual collection files: `admins.json`, `applications.json`, etc.

### Import Input
- `firestore_import/` directory (or custom name)
- Collection JSON files in the same format as export output
- Interactive selection of which collections to import

## 🔒 Security

### Export Tool
- **Read-only**: No write operations
- **Local export**: Data stays on your machine
- **Sample limits**: Prevents excessive data download
- **Service account**: Uses proper Firebase authentication

### Import Tool
- **Safe import**: Multiple checks to prevent data loss
- **Dry-run mode**: Test imports without making changes
- **Production protection**: Blocks usage of `prod.json` files
- **Interactive selection**: Choose what to import
- **Confirmation prompts**: Multiple confirmations before live imports

## 📊 Example Output Structure

```json
{
  "project_id": "mantra-earn-production",
  "exported_at": "2025-01-11T...",
  "total_collections": 6,
  "collections": {
    "users": {
      "collection_name": "users",
      "estimated_document_count": "100+",
      "sample_documents": [
        {
          "id": "user123",
          "data": {
            "email": "user@example.com",
            "createdAt": 1641234567.0
          }
        }
      ]
    }
  }
}
```

## ⚙️ Configuration

### Export Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `FIREBASE_SERVICE_ACCOUNT_PATH` | Required | Path to Firebase service account JSON |
| `SAMPLE_LIMIT` | 5 | Number of sample documents per collection |
| `OUTPUT_DIR` | firestore_export | Output directory name |

### Import Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FIREBASE_SERVICE_ACCOUNT_PATH` | ✅ | - | Path to service account JSON |
| `FIREBASE_PROJECT_ID` | ✅ | - | Target Firebase project ID |
| `IMPORT_DIR` | ❌ | `firestore_import` | Directory containing JSON files |
| `DRY_RUN` | ❌ | `false` | Enable dry-run mode |

## 🛡️ Import Safety Features

The import tool performs several safety checks:

1. **Service Account Validation**
   - Prevents using `prod.json` (production protection)
   - Verifies file exists and is readable

2. **Project Validation**
   - Confirms target project ID is set
   - Shows project name in all confirmations

3. **Data Validation**
   - Checks import directory exists
   - Validates JSON file format
   - Counts available collections

4. **Import Confirmation**
   - Shows summary before importing
   - Requires explicit confirmation for live imports
   - Allows cancellation at any step

## 🔍 Dry-Run Mode

Test your import without making any changes:

```bash
export DRY_RUN=true
./run_import.sh
```

This will:
- Validate all files and connections
- Show what would be imported
- Generate a simulation report
- Make no actual changes to the database

## 📊 Interactive Selection

The import tool will show you available collections and let you choose:

```
📋 Available collections for import:
   1. admins
   2. applications
   3. pools
   4. users

💡 Enter collection numbers (1-4) separated by commas,
   or 'all' to import all collections, or 'quit' to exit:
👉 Your selection: 1,3,4
```

Options:
- `1,3,4` - Import specific collections
- `all` - Import all available collections
- `quit` - Cancel the import

## 📋 Import Reports

After each import, the tool generates:

- **Console Output**: Real-time progress and results
- **Import Report**: JSON file with detailed statistics saved in `firestore_import_reports/`
- **Error Logs**: Any issues encountered during import

Example report location:
```
firestore_import_reports/import_report_20250111_143022.json
```

The reports are automatically organized in a separate directory to keep them from interfering with collection files during future imports.

## 🔧 Troubleshooting

### Common Issues

1. **"Service account not found"**
   ```bash
   # Check the path is correct
   ls -la $FIREBASE_SERVICE_ACCOUNT_PATH
   ```

2. **"No collection files found"**
   ```bash
   # Check the import directory
   ls -la firestore_import/
   ```

3. **"Cannot use prod.json"**
   - This is intentional! Use a different service account
   - Rename your file or use staging/dev credentials

4. **"Permission denied"**
   ```bash
   # Make sure the scripts are executable
   chmod +x run_export.sh run_import.sh
   ```

## 🔄 Workflow

This import tool is designed to work with the export tool:

1. **Export**: `./run_export.sh` → Creates JSON files in `firestore_export/`
2. **Move**: Copy files from `firestore_export/` to `firestore_import/`
3. **Import**: `./run_import.sh` → Imports from `firestore_import/`

This workflow allows you to safely transfer data between Firebase projects.

## 🎯 Next Steps

After running export:
1. Review the JSON structure
2. Understand your data model
3. Create your new database schema
4. Use the samples as templates

After running import:
1. Review import reports
2. Verify data integrity
3. Test your application
4. Monitor for any issues

## ⚠️ Important Notes

- **Always use dry-run mode first** to test your import
- **Never use the production service account** (prod.json is blocked)
- **Backup your target database** before importing
- **Review import reports** to ensure data integrity
- **Test with small datasets** before large imports

## 🆘 Emergency Procedures

If something goes wrong during import:

1. **Stop the process** (Ctrl+C if running)
2. **Check the import report** for what was imported
3. **Review the target database** to assess impact
4. **Use backup data** to restore if necessary
5. **Contact team** for assistance if needed

The tool is designed to be safe, but always have a backup plan!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.