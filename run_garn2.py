#!/usr/bin/env python3
"""
Script to convert PDB files to GARN models using GARN2.jar
For each molecule subfolder in GARN2/:
  1. Find the corresponding PDB file in PDB/
  2. Find the corresponding secondary structure in SECONDARY/
  3. Copy PDB to workspace root (where GARN2.jar is)
  4. Run: java -jar ./GARN2.jar PDBTOGARN {mol_id} {fasta_file} {pdb_file}
  5. Move outputs to GARN2/{mol_id}/
  6. Delete the copied PDB file
"""

import subprocess
import shutil
from pathlib import Path
import tempfile
import os

BASE_DIR = Path("/Users/jhonatan/Downloads/casp-predictions")
GARN2_JAR = BASE_DIR / "GARN2.jar"
GARN2_DIR = BASE_DIR / "GARN2"
PDB_DIR = BASE_DIR / "PDB"
SECONDARY_DIR = BASE_DIR / "SECONDARY"
JAVA7_BIN = Path("/Users/jhonatan/.sdkman/candidates/java/7.0.312-zulu/bin/java")

def get_molecule_id_from_pdb(pdb_file):
    """Extract molecule ID from PDB filename"""
    name = pdb_file.stem.lower()
    # Try to match first 4 alphanumeric characters
    if len(name) >= 4:
        candidate = name[:4].upper()
        # Check if secondary file exists
        secondary_file = SECONDARY_DIR / f"{candidate.lower()}.txt"
        if secondary_file.exists():
            return candidate
    return None

def main():
    print("=" * 60)
    print("GARN2 PDB to GARN Conversion")
    print("=" * 60)
    
    if not GARN2_JAR.exists():
        print(f"❌ GARN2.jar not found at {GARN2_JAR}")
        return
    
    if not GARN2_DIR.exists():
        print(f"❌ GARN2 folder not found at {GARN2_DIR}")
        return
    
    if not PDB_DIR.exists():
        print(f"❌ PDB folder not found at {PDB_DIR}")
        return
    
    # Get all molecule folders in GARN2
    mol_folders = sorted([d for d in GARN2_DIR.iterdir() if d.is_dir() and not d.name.startswith('.')])
    
    if not mol_folders:
        print("❌ No molecule folders found in GARN2/")
        return
    
    total_processed = 0
    total_failed = 0
    
    for mol_dir in mol_folders:
        mol_id = mol_dir.name.upper()
        print(f"\n🔍 Processing {mol_id}...")
        
        # Find corresponding PDB file
        pdb_candidates = list(PDB_DIR.glob(f"{mol_id.lower()}*.pdb"))
        
        if not pdb_candidates:
            print(f"  ⚠️  No PDB file found for {mol_id}")
            total_failed += 1
            continue
        
        pdb_file = pdb_candidates[0]
        print(f"  📄 Found PDB: {pdb_file.name}")
        
        # Find corresponding secondary structure file
        secondary_file = SECONDARY_DIR / f"{mol_id.lower()}.txt"
        
        if not secondary_file.exists():
            print(f"  ⚠️  No secondary structure file found: {secondary_file.name}")
            total_failed += 1
            continue
        
        print(f"  📋 Found secondary: {secondary_file.name}")
        
        # Copy PDB to workspace root
        pdb_copy = BASE_DIR / pdb_file.name
        try:
            shutil.copy2(str(pdb_file), str(pdb_copy))
            print(f"  📋 Copied PDB to workspace root")
        except Exception as e:
            print(f"  ❌ Failed to copy PDB: {e}")
            total_failed += 1
            continue
        
        # Run GARN2.jar
        cmd = [
            str(JAVA7_BIN),
            "-jar",
            str(GARN2_JAR),
            "PDBTOGARN",
            mol_id,
            str(secondary_file),
            str(pdb_copy),
        ]
        
        print(f"  ⚙️  Running GARN2.jar...")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(BASE_DIR),
                capture_output=True,
                timeout=300,
                text=True,
            )
            
            if result.returncode == 0:
                # Look for generated files
                garn_file = BASE_DIR / f"{mol_id}_GARN.csv"
                listnucleo_file = BASE_DIR / f"{mol_id}_listNucleo.csv"
                
                moved_count = 0
                
                # Move GARN file
                if garn_file.exists():
                    dest = mol_dir / garn_file.name
                    shutil.move(str(garn_file), str(dest))
                    moved_count += 1
                    print(f"    ✓ Moved {garn_file.name}")
                
                # Move listNucleo file
                if listnucleo_file.exists():
                    dest = mol_dir / listnucleo_file.name
                    shutil.move(str(listnucleo_file), str(dest))
                    moved_count += 1
                    print(f"    ✓ Moved {listnucleo_file.name}")
                
                if moved_count > 0:
                    print(f"  ✅ Conversion successful ({moved_count} files moved)")
                    total_processed += 1
                else:
                    print(f"  ⚠️  No output files generated")
                    total_failed += 1
            else:
                print(f"  ❌ GARN2.jar failed")
                if result.stderr:
                    err_msg = result.stderr.split('\n')[0][:100]
                    print(f"     {err_msg}")
                total_failed += 1
        
        except subprocess.TimeoutExpired:
            print(f"  ⏱️  Timeout")
            total_failed += 1
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:100]}")
            total_failed += 1
        
        finally:
            # Delete the copied PDB file
            if pdb_copy.exists():
                try:
                    pdb_copy.unlink()
                    print(f"  🗑️  Deleted copied PDB")
                except Exception as e:
                    print(f"  ⚠️  Failed to delete copied PDB: {e}")
    
    print("\n" + "=" * 60)
    print(f"✅ Successfully processed: {total_processed}")
    print(f"❌ Failed: {total_failed}")
    print("=" * 60)


if __name__ == "__main__":
    main()
