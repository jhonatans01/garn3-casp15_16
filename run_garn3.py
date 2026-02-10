#!/usr/bin/env python3
"""
Script to generate GARN models for all PDB files in prediction folders.
Uses GARN3.jar to convert PDB files to GARN models.
"""

import os
import subprocess
import sys
import shutil
import re
from pathlib import Path
from collections import defaultdict

# Base directory
BASE_DIR = Path("/Users/jhonatan/Downloads/casp-predictions")

# Prediction tool folders to process
PREDICTION_FOLDERS = [
    "AlphaFold",
    "FARFAR2",
    "FebRNA",
    "iFoldRNA",
    "NAST",
    "RNAComposer",
    "SimRNA",
    "trRosettaRNA",
    "x3dRNA",
    "Vfold",
    "MC-Sym",
]

# GARN3.jar location
GARN_JAR = BASE_DIR / "GARN3.jar"
SECONDARY_DIR = BASE_DIR / "SECONDARY"


def get_molecule_id_from_pdb(pdb_file):
    """Extract molecule ID from PDB filename (e.g., 7QR3 from 7QR3_A.pdb or 9C75-0001.pdb)"""
    filename = pdb_file.stem  # Remove .pdb extension
    # 1) Try first 4 alphanumeric chars (regular PDB-style id)
    match = re.match(r'^([A-Za-z0-9]{4})', filename)
    if match:
        candidate = match.group(1).lower()
        # Verify corresponding secondary file exists
        if (SECONDARY_DIR / f"{candidate}.txt").exists():
            return candidate

    # 2) Check ancestor directory names (common for tools that put PDBs under a folder named by the PDB id)
    for parent in pdb_file.parents:
        # stop at BASE_DIR
        if parent == BASE_DIR.parent:
            break
        name = parent.name
        # If parent name looks like a 4-char pdb id, test for secondary file
        if re.match(r'^[A-Za-z0-9]{4}$', name):
            candidate = name.lower()
            if (SECONDARY_DIR / f"{candidate}.txt").exists():
                return candidate

    # 3) If ancestor folder name doesn't match 4-char pattern, check if any ancestor's name matches a secondary file
    for parent in pdb_file.parents:
        if parent == BASE_DIR.parent:
            break
        candidate = parent.name.lower()
        if (SECONDARY_DIR / f"{candidate}.txt").exists():
            return candidate

    # 4) Fallback to previous behavior: split on underscore and take first part
    return filename.split("_")[0].lower()


def get_secondary_file(molecule_id):
    """Find corresponding FASTA file in SECONDARY folder"""
    secondary_file = SECONDARY_DIR / f"{molecule_id}.txt"
    return secondary_file if secondary_file.exists() else None


def create_output_folder(tool_name):
    """Create output folder for a tool (e.g., AlphaFold_GARN)"""
    output_dir = BASE_DIR / f"{tool_name}_GARN"
    output_dir.mkdir(exist_ok=True)
    return output_dir


def process_tool_folder(tool_name, start_idx=None):
    """Process all PDB files in a tool folder"""
    tool_dir = BASE_DIR / tool_name
    
    if not tool_dir.exists():
        print(f"⚠️  {tool_name} folder not found, skipping...")
        return 0, 0
    
    output_dir = create_output_folder(tool_name)
    processed = 0
    failed = 0
    
    print(f"\n🔍 Processing {tool_name}...")
    
    # Find all .pdb files in the tool folder
    pdb_files = list(tool_dir.rglob("*.pdb"))
    
    if not pdb_files:
        print(f"  No PDB files found in {tool_name}")
        return 0, 0
    
    pdb_files = sorted(pdb_files)
    
    # Resume from specific index if provided
    if start_idx is not None:
        pdb_files = pdb_files[start_idx:]
    
    print(f"  Found {len(pdb_files)} PDB files (processing {len(pdb_files)} total)")
    
    for idx, pdb_file in enumerate(pdb_files, start=start_idx or 0):
        # Get molecule ID (e.g., 7QR3)
        molecule_id = get_molecule_id_from_pdb(pdb_file)
        
        # Find corresponding SECONDARY file
        secondary_file = get_secondary_file(molecule_id)
        
        if not secondary_file:
            print(f"  [{idx}] ❌ No SECONDARY file for {pdb_file.name}")
            failed += 1
            continue
        
        # Create output subdirectory for this molecule
        molecule_output_dir = output_dir / molecule_id.upper()
        molecule_output_dir.mkdir(exist_ok=True)

        # Prepare names
        pdb_name = pdb_file.stem  # e.g., 7QR3_A

        # Run GARN3 in an isolated temporary directory to avoid file overwrites
        import tempfile
        try:
            with tempfile.TemporaryDirectory(prefix="garn_run_") as tmpdir:
                tmpdir_path = Path(tmpdir)

                # copy pdb and fasta into temp dir
                tmp_pdb = tmpdir_path / pdb_file.name
                tmp_fasta = tmpdir_path / f"{pdb_name}_fasta.txt"
                shutil.copy2(str(pdb_file), str(tmp_pdb))
                shutil.copy2(str(secondary_file), str(tmp_fasta))

                # command that runs inside tmpdir (use local filenames)
                cmd = [
                    "java",
                    "-jar",
                    str(GARN_JAR),
                    "PDBTOGARN",
                    pdb_name,
                    str(tmp_fasta.name),
                    str(tmp_pdb.name),
                ]

                try:
                    result = subprocess.run(
                        cmd,
                        cwd=str(tmpdir_path),
                        capture_output=True,
                        timeout=120,
                        text=True,
                    )

                    if result.returncode == 0:
                        print(f"  [{idx}] ✅ {pdb_file.name}")
                        processed += 1

                        # Move generated files from tmpdir to molecule output dir
                        # GARN jar removes dots/underscores from pdb_name when creating output files
                        # e.g., "3dRNA_DNA.pred1.min" becomes "3dRNA_DNApred1min"
                        sanitized_name = pdb_name.replace(".", "").replace("-", "")
                        
                        # Try the expected filename first, then the sanitized version
                        garn_file = tmpdir_path / f"{pdb_name}_GARN.csv"
                        if not garn_file.exists():
                            garn_file = tmpdir_path / f"{sanitized_name}_GARN.csv"
                        
                        listnucleo_file = tmpdir_path / f"{pdb_name}_listNucleo.csv"
                        if not listnucleo_file.exists():
                            listnucleo_file = tmpdir_path / f"{sanitized_name}_listNucleo.csv"

                        if garn_file.exists():
                            shutil.move(str(garn_file), str(molecule_output_dir / f"{pdb_name}_GARN.csv"))
                        if listnucleo_file.exists():
                            shutil.move(str(listnucleo_file), str(molecule_output_dir / f"{pdb_name}_listNucleo.csv"))

                    else:
                        print(f"  [{idx}] ❌ Failed: {pdb_file.name}")
                        if result.stderr:
                            err_msg = result.stderr.split('\n')[0][:160]
                            print(f"     {err_msg}")
                        failed += 1

                except subprocess.TimeoutExpired:
                    print(f"  [{idx}] ⏱️  Timeout: {pdb_file.name}")
                    failed += 1
                except Exception as e:
                    print(f"  [{idx}] ❌ Error: {pdb_file.name}: {str(e)[:160]}")
                    failed += 1

        except Exception as e:
            print(f"  [{idx}] ❌ Could not prepare temp dir or copy files: {e}")
            failed += 1
    
    return processed, failed


def main():
    """Main function"""
    print("=" * 60)
    print("GARN3 Model Generation")
    print("=" * 60)
    
    if not GARN_JAR.exists():
        print(f"❌ GARN3.jar not found at {GARN_JAR}")
        sys.exit(1)
    
    if not SECONDARY_DIR.exists():
        print(f"❌ SECONDARY folder not found at {SECONDARY_DIR}")
        sys.exit(1)
    
    total_processed = 0
    total_failed = 0
    
    # Allow optional tool filter: python3 run_garn3.py x3dRNA
    tools_to_process = PREDICTION_FOLDERS
    if len(sys.argv) > 1:
        tools_to_process = [tool for tool in PREDICTION_FOLDERS if tool.lower() == sys.argv[1].lower()]
        if not tools_to_process:
            print(f"❌ Tool '{sys.argv[1]}' not found in {PREDICTION_FOLDERS}")
            sys.exit(1)
    
    for tool_name in tools_to_process:
        processed, failed = process_tool_folder(tool_name)
        total_processed += processed
        total_failed += failed
    
    print("\n" + "=" * 60)
    print(f"✅ Total Processed: {total_processed}")
    print(f"❌ Total Failed: {total_failed}")
    print("=" * 60)


if __name__ == "__main__":
    main()
