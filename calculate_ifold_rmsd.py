#!/usr/bin/env python3
"""
Script to calculate RMSD values for iFoldRNA predictions.
For each molecule, uses cluster1_GARN.csv as reference and compares against other clusters.
Runs: java -jar ./GARN2.jar RMSD {mol_name} {reference_csv} {predicted_csv1} {predicted_csv2} ...
Moves resulting {mol_name}_rmsd.csv to the respective iFoldRNA_GARN/{mol_name}/ folder.
"""

import subprocess
import sys
import shutil
from pathlib import Path

BASE_DIR = Path("/Users/jhonatan/Downloads/casp-predictions")
GARN2_JAR = BASE_DIR / "GARN2.jar"
IFOLD_DIR = BASE_DIR / "iFoldRNA_GARN"
JAVA7_BIN = Path("/Users/jhonatan/.sdkman/candidates/java/7.0.312-zulu/bin/java")


def main():
    """Main function"""
    print("=" * 60)
    print("iFoldRNA RMSD Calculation")
    print("=" * 60)
    
    if not GARN2_JAR.exists():
        print(f"❌ GARN2.jar not found at {GARN2_JAR}")
        sys.exit(1)
    
    if not JAVA7_BIN.exists():
        print(f"❌ Java 7 not found at {JAVA7_BIN}")
        sys.exit(1)
    
    total_processed = 0
    total_failed = 0
    
    # Iterate through iFoldRNA molecule folders
    ifold_mol_dirs = [d for d in IFOLD_DIR.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    for mol_dir in sorted(ifold_mol_dirs):
        mol_id = mol_dir.name.upper()
        
        print(f"\n🔍 Processing {mol_id}...")
        
        # Find reference file (cluster1_GARN.csv)
        ref_file = mol_dir / "cluster1_GARN.csv"
        
        if not ref_file.exists():
            print(f"  ⊘ Reference file not found: {ref_file.name}")
            continue
        
        # Find all other cluster files (cluster2_GARN.csv, cluster3_GARN.csv, etc.)
        predicted_files = sorted([f for f in mol_dir.glob("cluster*_GARN.csv") if f.name != ref_file.name])
        
        if not predicted_files:
            print(f"  ⊘ No additional cluster files found")
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
        
        print(f"  Running RMSD with {len(predicted_files)} cluster files...")
        
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
                    # Move to iFoldRNA_GARN output folder
                    dest = mol_dir / rmsd_file.name
                    shutil.move(str(rmsd_file), str(dest))
                    print(f"  ✅ RMSD calculated and moved to iFoldRNA_GARN/{mol_id}/{rmsd_file.name}")
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
