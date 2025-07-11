#!/usr/bin/env python3
"""
Mantra Finance Database Importer

This script imports collections from JSON files in the firestore_import folder
to a specified Firestore database.

ENVIRONMENT VARIABLES:
- FIREBASE_PROJECT_ID: Target Firebase project ID
- FIREBASE_SERVICE_ACCOUNT_PATH: Path to service account JSON file
- FIREBASE_DATABASE_NAME: Database name (optional, defaults to "default")
- IMPORT_DIR: Directory containing JSON files (optional, defaults to "firestore_import")
- DRY_RUN: Set to "true" for dry-run mode (optional, defaults to "false")

SAFETY FEATURES:
- Production service account protection
- Interactive collection selection
- Confirmation prompts
- Dry-run mode available
- Detailed logging
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import DocumentReference


class FirestoreImporter:
    """Safe Firestore database importer with safety checks."""
    
    def __init__(self, service_account_path: str, project_id: str, dry_run: bool = False, database_name: str = "(default)"):
        """Initialize the importer with Firebase credentials."""
        self.project_id = project_id
        self.service_account_path = service_account_path
        self.dry_run = dry_run
        self.database_name = database_name
        self.db: Any = None
        self._validate_service_account()
        self._init_firebase()
        
    def _validate_service_account(self):
        """Validate service account path and ensure it's not production."""
        if not os.path.exists(self.service_account_path):
            raise FileNotFoundError(f"Service account file not found: {self.service_account_path}")
        
        # Get filename from path
        filename = os.path.basename(self.service_account_path)
        
        # Safety check: prevent using production service account
        if filename.lower() == 'prod.json':
            raise ValueError(
                "🚨 SAFETY CHECK FAILED: Cannot use 'prod.json' service account for imports!\n"
                "This is a safety measure to prevent accidental modifications to production.\n"
                "Please use a different service account file."
            )
        
        print(f"✅ Service account validated: {filename}")
        
    def _init_firebase(self):
        """Initialize Firebase Admin SDK."""
        try:
            # Check if already initialized
            firebase_admin.get_app()
            firebase_admin.delete_app(firebase_admin.get_app())
        except ValueError:
            pass
        
        # Initialize with service account
        cred = credentials.Certificate(self.service_account_path)
        firebase_admin.initialize_app(cred, {
            'projectId': self.project_id,
        })
        
        # Connect to specific database
        if self.database_name == "(default)":
            self.db = firestore.client()
        else:
            self.db = firestore.client(database_id=self.database_name)
        
        mode = "DRY-RUN" if self.dry_run else "LIVE"
        db_info = f"database '{self.database_name}'" if self.database_name != "(default)" else "default database"
        print(f"✅ Connected to Firestore project: {self.project_id}, {db_info} ({mode} mode)")
    
    def _deserialize_firestore_data(self, data: Any) -> Any:
        """Convert JSON data back to Firestore-compatible types."""
        if isinstance(data, dict):
            return {key: self._deserialize_firestore_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._deserialize_firestore_data(item) for item in data]
        elif isinstance(data, str) and data.startswith("ref:"):
            # Handle document references - this is a simplified version
            # In a real scenario, you might want to create actual DocumentReference objects
            return data  # Keep as string for now
        else:
            return data
    
    def get_available_collections(self, import_dir: str = "firestore_import") -> List[str]:
        """Get list of available collections from JSON files in import directory."""
        import_path = Path(import_dir)
        
        if not import_path.exists():
            raise FileNotFoundError(f"Import directory not found: {import_path}")
        
        json_files = list(import_path.glob("*.json"))
        
        # Extract collection names from filenames (remove .json extension)
        collections = []
        for json_file in json_files:
            # Skip the complete database structure file and import reports
            if (json_file.name != "complete_database_structure.json" and 
                not json_file.name.startswith("import_report_")):
                collection_name = json_file.stem
                collections.append(collection_name)
        
        return sorted(collections)
    
    def load_collection_data(self, collection_name: str, import_dir: str = "firestore_import") -> Dict[str, Any]:
        """Load collection data from JSON file."""
        import_path = Path(import_dir)
        json_file = import_path / f"{collection_name}.json"
        
        if not json_file.exists():
            raise FileNotFoundError(f"Collection file not found: {json_file}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
    
    def import_collection(self, collection_name: str, import_dir: str = "firestore_import", 
                         overwrite: bool = False) -> Dict[str, Any]:
        """Import a single collection from JSON file."""
        print(f"📥 {'[DRY-RUN] ' if self.dry_run else ''}Importing collection: {collection_name}")
        
        # Load collection data
        collection_data = self.load_collection_data(collection_name, import_dir)
        
        if 'sample_documents' not in collection_data:
            raise ValueError(f"Invalid collection data format in {collection_name}.json")
        
        documents = collection_data['sample_documents']
        collection_ref = self.db.collection(collection_name)
        
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        for doc_info in documents:
            doc_id = doc_info['id']
            doc_data = self._deserialize_firestore_data(doc_info['data'])
            
            try:
                if not self.dry_run:
                    # Check if document exists
                    existing_doc = collection_ref.document(doc_id).get()
                    
                    if existing_doc.exists and not overwrite:
                        print(f"  ⏭️  Skipped existing document: {doc_id}")
                        skipped_count += 1
                        continue
                    
                    # Import the document
                    collection_ref.document(doc_id).set(doc_data)
                    imported_count += 1
                    print(f"  ✅ Imported document: {doc_id}")
                else:
                    print(f"  🔍 [DRY-RUN] Would import document: {doc_id}")
                    imported_count += 1
                
            except Exception as e:
                print(f"  ❌ Error importing document {doc_id}: {e}")
                error_count += 1
        
        result = {
            'collection_name': collection_name,
            'total_documents': len(documents),
            'imported': imported_count,
            'skipped': skipped_count,
            'errors': error_count,
            'imported_at': datetime.now().isoformat()
        }
        
        print(f"✅ Collection {collection_name} import completed:")
        print(f"   📊 Total: {result['total_documents']}, "
              f"Imported: {result['imported']}, "
              f"Skipped: {result['skipped']}, "
              f"Errors: {result['errors']}")
        
        return result
    
    def import_selected_collections(self, collection_names: List[str], 
                                  import_dir: str = "firestore_import",
                                  overwrite: bool = False) -> Dict[str, Any]:
        """Import multiple selected collections."""
        print(f"🚀 {'[DRY-RUN] ' if self.dry_run else ''}Starting import of {len(collection_names)} collections")
        
        results = {
            'project_id': self.project_id,
            'import_started_at': datetime.now().isoformat(),
            'dry_run': self.dry_run,
            'collections': {},
            'summary': {
                'total_collections': len(collection_names),
                'successful_imports': 0,
                'failed_imports': 0,
                'total_documents': 0,
                'total_imported': 0,
                'total_skipped': 0,
                'total_errors': 0
            }
        }
        
        for collection_name in collection_names:
            try:
                result = self.import_collection(collection_name, import_dir, overwrite)
                results['collections'][collection_name] = result
                results['summary']['successful_imports'] += 1
                results['summary']['total_documents'] += result['total_documents']
                results['summary']['total_imported'] += result['imported']
                results['summary']['total_skipped'] += result['skipped']
                results['summary']['total_errors'] += result['errors']
                
            except Exception as e:
                print(f"❌ Failed to import collection {collection_name}: {e}")
                results['collections'][collection_name] = {
                    'error': str(e),
                    'imported_at': datetime.now().isoformat()
                }
                results['summary']['failed_imports'] += 1
        
        results['import_completed_at'] = datetime.now().isoformat()
        
        # Save import report
        if not self.dry_run:
            # Create reports directory if it doesn't exist
            reports_dir = Path(import_dir).parent / "firestore_import_reports"
            reports_dir.mkdir(exist_ok=True)
            
            report_file = reports_dir / f"import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"📋 Import report saved: {report_file}")
        
        return results


def select_collections(available_collections: List[str]) -> List[str]:
    """Interactive collection selection."""
    if not available_collections:
        print("❌ No collections available for import.")
        return []
    
    print("\n📋 Available collections for import:")
    for i, collection in enumerate(available_collections, 1):
        print(f"  {i:2d}. {collection}")
    
    print(f"\n💡 Enter collection numbers (1-{len(available_collections)}) separated by commas,")
    print("   or 'all' to import all collections, or 'quit' to exit:")
    
    while True:
        user_input = input("👉 Your selection: ").strip().lower()
        
        if user_input == 'quit':
            return []
        
        if user_input == 'all':
            return available_collections
        
        try:
            # Parse comma-separated numbers
            indices = [int(x.strip()) for x in user_input.split(',')]
            selected = []
            
            for index in indices:
                if 1 <= index <= len(available_collections):
                    selected.append(available_collections[index - 1])
                else:
                    print(f"❌ Invalid selection: {index}. Please try again.")
                    break
            else:
                # All indices were valid
                return selected
                
        except ValueError:
            print("❌ Invalid input. Please enter numbers separated by commas, 'all', or 'quit'.")


def confirm_import(selected_collections: List[str], project_id: str, dry_run: bool, database_name: str = "(default)") -> bool:
    """Confirm import operation."""
    if not selected_collections:
        return False
    
    mode = "DRY-RUN (no changes will be made)" if dry_run else "LIVE IMPORT"
    
    print(f"\n🔍 Import Summary:")
    print(f"   Target Project: {project_id}")
    if database_name != "(default)":
        print(f"   Database: {database_name}")
    print(f"   Mode: {mode}")
    print(f"   Collections to import ({len(selected_collections)}):")
    for collection in selected_collections:
        print(f"     - {collection}")
    
    if dry_run:
        return True
    
    db_info = f" (database: {database_name})" if database_name != "(default)" else ""
    print(f"\n⚠️  This will import data to the '{project_id}' project{db_info}.")
    print("   Existing documents may be overwritten if you choose to overwrite.")
    
    while True:
        confirmation = input("\n👉 Proceed with import? (yes/no): ").strip().lower()
        if confirmation in ['yes', 'y']:
            return True
        elif confirmation in ['no', 'n']:
            return False
        else:
            print("Please enter 'yes' or 'no'.")


def main():
    """Main function to run the importer."""
    print("📥 Mantra Finance Database Importer")
    print("=" * 50)
    
    # Configuration
    PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
    SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    IMPORT_DIR = os.getenv("IMPORT_DIR", "firestore_import")
    DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
    DATABASE_NAME = os.getenv("FIREBASE_DATABASE_NAME", "default")

    if not PROJECT_ID:
        print("❌ Error: FIREBASE_PROJECT_ID environment variable not set")
        print("Please set it to your target Firebase project ID:")
        print("export FIREBASE_PROJECT_ID=your-project-id")
        sys.exit(1)
    
    if not SERVICE_ACCOUNT_PATH:
        print("❌ Error: FIREBASE_SERVICE_ACCOUNT_PATH environment variable not set")
        print("Please set it to the path of your Firebase service account JSON file:")
        print("export FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/service-account.json")
        sys.exit(1)
    
    try:
        # Initialize importer
        importer = FirestoreImporter(SERVICE_ACCOUNT_PATH, PROJECT_ID, DRY_RUN, DATABASE_NAME)
        
        # Get available collections
        available_collections = importer.get_available_collections(IMPORT_DIR)
        
        if not available_collections:
            print(f"❌ No collection files found in {IMPORT_DIR}/")
            print("Please ensure you have JSON files in the import directory.")
            sys.exit(1)
        
        # Interactive collection selection
        selected_collections = select_collections(available_collections)
        
        if not selected_collections:
            print("👋 Import cancelled or no collections selected.")
            sys.exit(0)
        
        # Confirm import
        if not confirm_import(selected_collections, PROJECT_ID, DRY_RUN, DATABASE_NAME):
            print("👋 Import cancelled.")
            sys.exit(0)
        
        # Ask about overwrite mode (only for live imports)
        overwrite = False
        if not DRY_RUN:
            overwrite_input = input("\n👉 Overwrite existing documents? (yes/no): ").strip().lower()
            overwrite = overwrite_input in ['yes', 'y']
        
        # Perform import
        results = importer.import_selected_collections(
            selected_collections, 
            IMPORT_DIR, 
            overwrite
        )
        
        # Print summary
        summary = results['summary']
        print(f"\n🎉 Import {'simulation' if DRY_RUN else 'operation'} completed!")
        print(f"   📊 Collections: {summary['successful_imports']}/{summary['total_collections']} successful")
        print(f"   📄 Documents: {summary['total_imported']} imported, {summary['total_skipped']} skipped, {summary['total_errors']} errors")
        
        if summary['failed_imports'] > 0:
            print(f"   ⚠️  {summary['failed_imports']} collections failed to import")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
