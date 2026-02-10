#!/usr/bin/env python3
"""
Script to calculate RMSD values for GARN3 predictions.
For each molecule, runs: java -jar ./GARN3.jar RMSD {mol_id} {reference_csv} {predicted_csv1} {predicted_csv2} ...
Moves resulting {mol_id}_rmsd.csv to the respective GARN3_GARN/{mol_id}/ folder.
"""

import subprocess
import sys
import shutil
from pathlib import Path

BASE_DIR = Path("/Users/jhonatan/Downloads/casp-predictions")
GARN3_JAR = BASE_DIR / "GARN3.jar"
REFERENCE_DIR = BASE_DIR / "REFERENCE_PBD"
GARN3_DIR = BASE_DIR / "GARN3_GARN"


def main():
    """Main function"""
    print("=" * 60)
    print("GARN3 RMSD Calculation")
    print("=" * 60)
    
    if not GARN3_JAR.exists():
        print(f"❌ GARN3.jar not found at {GARN3_JAR}")
        sys.exit(1)
    
    if not REFERENCE_DIR.exists():
        print(f"❌ REFERENCE_PBD folder not found at {REFERENCE_DIR}")
        sys.exit(1)
    
    # Find all reference GARN files
    reference_files = list(REFERENCE_DIR.glob("*/*_GARN.csv"))
    
    if not reference_files:
        print(f"❌ No reference GARN files found in {REFERENCE_DIR}")
        sys.exit(1)
    
    total_processed = 0
    total_failed = 0
    
    for ref_file in sorted(reference_files):
        mol_name = ref_file.parent.name
        mol_id = ref_file.stem.replace("_GARN", "").upper()  # e.g., 7QR3
        
        print(f"\n🔍 Processing {mol_id}...")
        
        # Check if GARN3 folder exists for this molecule
        garn3_mol_dir = GARN3_DIR / mol_id
        
        if not garn3_mol_dir.exists():
            print(f"  ⊘ GARN3_GARN/{mol_id}: not found")
            continue
        
        # Find all predicted GARN files in GARN3 folder
        # For GARN3, look for GARN_{mol_id}_*.csv pattern
        predicted_files = sorted(garn3_mol_dir.glob(f"GARN_{mol_id}_*.csv"))
        
        if not predicted_files:
            print(f"  ⊘ GARN3_GARN/{mol_id}: no predicted files")
            continue
        
        # Build command
        cmd = [
            "java",
            "-jar",
            str(GARN3_JAR),
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
                    # Move to GARN3 output folder
                    dest = garn3_mol_dir / rmsd_file.name
                    shutil.move(str(rmsd_file), str(dest))
                    print(f"  ✅ RMSD calculated and moved to GARN3_GARN/{mol_id}/{rmsd_file.name}")
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
