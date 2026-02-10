#!/usr/bin/env python3
"""
Script to calculate RMSD values comparing reference structures against predicted structures.
For each molecule, runs: java -jar ./GARN2.jar RMSD {mol_name} {reference_csv} {predicted_csv1} {predicted_csv2} ...
Moves resulting {mol_name}_rmsd.csv to the respective GARN2/{mol_name}/ folder.
"""

import subprocess
import sys
import shutil
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path("/Users/jhonatan/Downloads/casp-predictions")
GARN2_JAR = BASE_DIR / "GARN2.jar"
REFERENCE_DIR = BASE_DIR / "REFERENCE_PBD"
GARN2_DIR = BASE_DIR / "GARN2"
JAVA7_BIN = Path("/Users/jhonatan/.sdkman/candidates/java/7.0.312-zulu/bin/java")


def main():
    """Main function"""
    print("=" * 60)
    print("GARN2 RMSD Calculation")
    print("=" * 60)
    
    if not GARN2_JAR.exists():
        print(f"❌ GARN2.jar not found at {GARN2_JAR}")
        sys.exit(1)
    
    if not JAVA7_BIN.exists():
        print(f"❌ Java 7 not found at {JAVA7_BIN}")
        sys.exit(1)
    
    total_processed = 0
    total_failed = 0
    
    # Iterate through GARN2 molecule folders
    garn2_mol_dirs = [d for d in GARN2_DIR.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    for mol_dir in sorted(garn2_mol_dirs):
        mol_id = mol_dir.name.upper()
        
        print(f"\n🔍 Processing {mol_id}...")
        
        # Find reference file (mol_id_GARN.csv in GARN2 folder) - case insensitive search
        ref_file = None
        for f in mol_dir.glob("*_GARN.csv"):
            if f.stem.upper().replace("_GARN", "") == mol_id:
                ref_file = f
                break
        
        if ref_file is None:
            print(f"  ⊘ Reference file not found: {mol_id}_GARN.csv")
            continue
        
        # Find all other files: either *_GARN.csv or GARN_*.csv (excluding the reference)
        predicted_files = []
        for f in mol_dir.glob("*_GARN.csv"):
            if f != ref_file:
                predicted_files.append(f)
        for f in mol_dir.glob(f"GARN_{mol_id.lower()}_*.csv"):
            predicted_files.append(f)
        
        predicted_files = sorted(set(predicted_files))
        
        if not predicted_files:
            print(f"  ⊘ No additional predicted files found")
            continue
        
        # Build command
        cmd = [
            str(JAVA7_BIN),
            "-jar",
            str(GARN2_JAR),
            "RMSD",
            mol_id,
            str(ref_file),
        ]
        
        # Add all predicted files
        cmd.extend(str(p) for p in predicted_files)
        
        print(f"  Running RMSD with {len(predicted_files)} predicted files...")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(BASE_DIR),
                capture_output=True,
                timeout=300,
                text=True,
            )
            
            if result.returncode == 0:
                # Look for generated {mol_id}_rmsd.csv file
                rmsd_file = BASE_DIR / f"{mol_id}_rmsd.csv"
                
                if rmsd_file.exists():
                    # Move to GARN2 output folder
                    dest = mol_dir / rmsd_file.name
                    shutil.move(str(rmsd_file), str(dest))
                    print(f"  ✅ RMSD calculated and moved to GARN2/{mol_id}/{rmsd_file.name}")
                    total_processed += 1
                else:
                    print(f"  ⚠️  RMSD command succeeded but no output file found")
                    total_failed += 1
            else:
                print(f"  ❌ RMSD calculation failed")
                if result.stderr:
                    err_msg = result.stderr.split('\n')[0][:100]
                    print(f"     {err_msg}")
                total_failed += 1
        
        except subprocess.TimeoutExpired:
            print(f"  ⏱️  Timeout")
            total_failed += 1
        except Exception as e:
            print(f"  ❌ Error - {str(e)[:100]}")
            total_failed += 1
    
    print("\n" + "=" * 60)
    print(f"✅ RMSD Calculations Completed: {total_processed}")
    print(f"❌ RMSD Calculations Failed: {total_failed}")
    print("=" * 60)


if __name__ == "__main__":
    main()
