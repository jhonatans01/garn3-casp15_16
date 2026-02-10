#!/usr/bin/env python3
"""
Move cluster GARN files from iFoldRNA to iFoldRNA_GARN
"""

import shutil
from pathlib import Path

BASE_DIR = Path("/Users/jhonatan/Downloads/casp-predictions")
IFOLD_SOURCE = BASE_DIR / "iFoldRNA"
IFOLD_GARN = BASE_DIR / "iFoldRNA_GARN"

print("=" * 60)
print("Moving cluster GARN files to iFoldRNA_GARN")
print("=" * 60)

moved_count = 0

# Iterate through all molecule folders
for mol_dir in sorted([d for d in IFOLD_SOURCE.iterdir() if d.is_dir()]):
    mol_id = mol_dir.name
    
    # Find all cluster*_GARN.csv files
    garn_files = sorted(mol_dir.glob("cluster*_GARN.csv"))
    
    if not garn_files:
        continue
    
    print(f"\n📁 {mol_id}:")
    
    # Get or create the target directory
    target_dir = IFOLD_GARN / mol_id
    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)
    
    for garn_file in garn_files:
        try:
            dest = target_dir / garn_file.name
            shutil.copy2(str(garn_file), str(dest))
            print(f"  ✅ Copied {garn_file.name}")
            moved_count += 1
        except Exception as e:
            print(f"  ❌ Error copying {garn_file.name}: {e}")

print("\n" + "=" * 60)
print(f"✅ Total files copied: {moved_count}")
print("=" * 60)
