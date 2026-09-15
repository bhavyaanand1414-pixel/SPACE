import os
import shutil
from pathlib import Path
import sys

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.ingestion import IngestionService
from app.core.config import settings
from app.core.logging import logger

def migrate_database():
    """
    Safely migrate the FAISS vector index when changing the embedding model
    (e.g., from standard CLIP to RemoteCLIP).
    """
    print("=======================================")
    print("  SIH1518: VECTOR DB MIGRATION TOOL")
    print("=======================================")
    
    old_index_dir = Path(settings.FAISS_INDEX_PATH)
    backup_dir = old_index_dir.parent / f"{old_index_dir.name}_backup"
    
    if old_index_dir.exists():
        print(f"  Backing up old index to {backup_dir}...")
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        shutil.copytree(old_index_dir, backup_dir)
        
        # Clear the old index directory so FAISS re-initializes
        for file in old_index_dir.glob("*"):
            if file.is_file():
                file.unlink()
        print("  Cleared old index.")
    
    # Re-ingest data
    scenes_dir = settings.SCENES_STORAGE_PATH
    print(f"  Starting re-ingestion from {scenes_dir} using model: {settings.EMBEDDING_PRETRAINED}...")
    
    try:
        results = IngestionService.ingest_directory(scenes_dir)
        
        success = sum(1 for r in results if r.status == "completed")
        failed = sum(1 for r in results if r.status == "failed")
        
        print("\n  Migration Results:")
        print(f"   Scenes processed : {len(results)}")
        print(f"   Successfully     : {success}")
        print(f"   Failed           : {failed}")
        
        for r in results:
            if r.status == "failed":
                print(f"    {r.filename} - Error: {r.error}")
                
        print("\n  Migration complete.")
        
    except Exception as e:
        print(f"\n  Migration failed: {str(e)}")
        print(f"  Restoring backup from {backup_dir}...")
        if old_index_dir.exists():
            shutil.rmtree(old_index_dir)
        shutil.copytree(backup_dir, old_index_dir)
        print("🔙 Backup restored.")

if __name__ == "__main__":
    migrate_database()
