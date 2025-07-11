#!/usr/bin/env python3
"""
Mantra Finance Database Structure Exporter

This script safely exports the structure and sample data from the production
Firestore database to help understand the data model for creating new databases.

SAFETY FEATURES:
- Read-only operations only
- No write capabilities 
- Exports to local JSON files
- Sample data only (configurable limits)
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import DocumentSnapshot


class FirestoreExporter:
    """Safe read-only Firestore database exporter."""
    
    def __init__(self, service_account_path: str, project_id: str):
        """Initialize the exporter with Firebase credentials."""
        self.project_id = project_id
        self.service_account_path = service_account_path
        self.db = None
        self._init_firebase()
        
    def _init_firebase(self):
        """Initialize Firebase Admin SDK."""
        try:
            # Check if already initialized
            firebase_admin.get_app()
        except ValueError:
            # Initialize with service account
            cred = credentials.Certificate(self.service_account_path)
            firebase_admin.initialize_app(cred, {
                'projectId': self.project_id,
            })
        
        self.db = firestore.client()
        print(f"✅ Connected to Firestore project: {self.project_id}")
    
    def _document_to_dict(self, doc: DocumentSnapshot) -> Dict[str, Any]:
        """Convert Firestore document to dictionary, handling special types."""
        if not doc.exists:
            return {}
            
        data = doc.to_dict()
        if not data:
            return {}
            
        # Convert Firestore types to JSON-serializable types
        return self._serialize_firestore_data(data)
    
    def _serialize_firestore_data(self, data: Any) -> Any:
        """Recursively serialize Firestore data types to JSON-compatible types."""
        if isinstance(data, dict):
            return {key: self._serialize_firestore_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._serialize_firestore_data(item) for item in data]
        elif hasattr(data, 'timestamp'):  # Firestore timestamp
            return data.timestamp()
        elif hasattr(data, 'id'):  # Document reference
            return f"ref:{data.id}"
        else:
            return data
    
    def get_collections(self) -> List[str]:
        """Get list of all collections in the database."""
        collections = []
        for collection in self.db.collections():
            collections.append(collection.id)
        return sorted(collections)
    
    def export_collection_structure(self, collection_name: str, sample_limit: int = 5) -> Dict[str, Any]:
        """Export collection structure with sample documents."""
        print(f"📊 Analyzing collection: {collection_name}")
        
        collection_ref = self.db.collection(collection_name)
        
        # Get sample documents
        docs = collection_ref.limit(sample_limit).stream()
        sample_docs = []
        
        for doc in docs:
            doc_data = self._document_to_dict(doc)
            if doc_data:  # Only include non-empty documents
                sample_docs.append({
                    'id': doc.id,
                    'data': doc_data
                })
        
        # Get collection stats
        try:
            # This is a rough estimate - Firestore doesn't provide exact counts easily
            all_docs = list(collection_ref.limit(100).stream())
            estimated_count = len(all_docs)
            if len(all_docs) == 100:
                estimated_count = "100+"
        except Exception as e:
            estimated_count = "unknown"
            print(f"⚠️  Could not get document count for {collection_name}: {e}")
        
        return {
            'collection_name': collection_name,
            'estimated_document_count': estimated_count,
            'sample_documents': sample_docs,
            'sample_count': len(sample_docs),
            'exported_at': datetime.now().isoformat()
        }
    
    def export_database_structure(self, output_dir: str = "firestore_export", sample_limit: int = 5) -> Dict[str, Any]:
        """Export entire database structure."""
        print(f"🚀 Starting database export to: {output_dir}")
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Get all collections
        collections = self.get_collections()
        print(f"📋 Found {len(collections)} collections: {', '.join(collections)}")
        
        database_structure = {
            'project_id': self.project_id,
            'exported_at': datetime.now().isoformat(),
            'total_collections': len(collections),
            'collections': {}
        }
        
        # Export each collection
        for collection_name in collections:
            try:
                collection_data = self.export_collection_structure(collection_name, sample_limit)
                database_structure['collections'][collection_name] = collection_data
                
                # Save individual collection file
                collection_file = output_path / f"{collection_name}.json"
                with open(collection_file, 'w', encoding='utf-8') as f:
                    json.dump(collection_data, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Exported {collection_name} ({collection_data['sample_count']} samples)")
                
            except Exception as e:
                print(f"❌ Error exporting {collection_name}: {e}")
                database_structure['collections'][collection_name] = {
                    'error': str(e),
                    'exported_at': datetime.now().isoformat()
                }
        
        # Save complete database structure
        complete_file = output_path / "complete_database_structure.json"
        with open(complete_file, 'w', encoding='utf-8') as f:
            json.dump(database_structure, f, indent=2, ensure_ascii=False)
        
        print(f"🎉 Database export completed! Files saved to: {output_path.absolute()}")
        return database_structure


def main():
    """Main function to run the exporter."""
    print("🔥 Mantra Finance Database Exporter")
    print("=" * 50)
    
    # Configuration
    PROJECT_ID = "mantra-earn-production"  # From your .firebaserc
    SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    
    if not SERVICE_ACCOUNT_PATH:
        print("❌ Error: FIREBASE_SERVICE_ACCOUNT_PATH environment variable not set")
        print("Please set it to the path of your Firebase service account JSON file:")
        print("export FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/service-account.json")
        sys.exit(1)
    
    if not os.path.exists(SERVICE_ACCOUNT_PATH):
        print(f"❌ Error: Service account file not found: {SERVICE_ACCOUNT_PATH}")
        sys.exit(1)
    
    try:
        # Initialize exporter
        exporter = FirestoreExporter(SERVICE_ACCOUNT_PATH, PROJECT_ID)
        
        # Export database
        sample_limit = int(os.getenv("SAMPLE_LIMIT", "5"))
        output_dir = os.getenv("OUTPUT_DIR", "firestore_export")
        
        database_structure = exporter.export_database_structure(
            output_dir=output_dir,
            sample_limit=sample_limit
        )
        
        print("\n📊 Export Summary:")
        print(f"   Project: {database_structure['project_id']}")
        print(f"   Collections: {database_structure['total_collections']}")
        print(f"   Output directory: {output_dir}")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()