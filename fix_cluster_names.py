#!/usr/bin/env python3
"""
Rename cluster files with dots in their names to remove the dot notation.
For example: cluster.1_GARN.csv -> cluster1_GARN.csv
"""

import os
from pathlib import Path

BASE_DIR = Path("/Users/jhonatan/Downloads/casp-predictions")
FOLDERS = ["iFoldRNA", "iFoldRNA_GARN"]

def rename_files_in_folder(folder_path):
    """Rename files with cluster.X pattern to clusterX pattern"""
    
    if not folder_path.exists():
        print(f"⚠️  Folder not found: {folder_path}")
        return 0
    
    renamed_count = 0
    
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # Look for files with pattern like "cluster.1", "cluster.2", etc.
            if "cluster." in file:
                # Replace cluster.X with clusterX
                new_name = file.replace("cluster.", "cluster")
                
                if new_name != file:
                    old_path = Path(root) / file
                    new_path = Path(root) / new_name
                    
                    try:
                        old_path.rename(new_path)
                        print(f"✅ Renamed: {file} -> {new_name}")
                        renamed_count += 1
                    except Exception as e:
                        print(f"❌ Error renaming {file}: {e}")
    
    return renamed_count

print("=" * 60)
print("Fixing cluster file names (removing dots)")
print("=" * 60)

total_renamed = 0

for folder_name in FOLDERS:
    folder_path = BASE_DIR / folder_name
    print(f"\n📁 Processing {folder_name}...")
    count = rename_files_in_folder(folder_path)
    total_renamed += count
    print(f"   Renamed: {count} files")

print("\n" + "=" * 60)
print(f"✅ Total files renamed: {total_renamed}")
print("=" * 60)
