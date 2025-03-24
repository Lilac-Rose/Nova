import json
from pathlib import Path
import shutil
import sqlite3
from datetime import datetime

def backup_and_clean():
    """Backup and remove old JSON files"""
    backup_dir = Path("json/backups")
    backup_dir.mkdir(exist_ok=True)
    
    old_files = [
        "sparkles.json",
        "xp.json", 
        "coins.json"
    ]
    
    for filename in old_files:
        path = Path(f"json/{filename}")
        if path.exists():
            # Create timestamped backup
            backup_path = backup_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            shutil.copy2(path, backup_path)
            print(f"Backed up {filename} to {backup_path}")
            
            # Remove original
            path.unlink()
            print(f"Removed {filename}")

if __name__ == "__main__":
    print("Starting cleanup...")
    backup_and_clean()
    print("Cleanup complete!")