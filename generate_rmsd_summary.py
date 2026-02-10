#!/usr/bin/env python3
"""
Generate a single CSV summary of min/max RMSD per technique and molecule.
- Scans all folders matching "*_GARN" under BASE_DIR
- For each molecule subfolder, finds the first *_rmsd.csv file
- Parses numeric RMSD values from the appropriate column:
    - If technique name contains 'GARN3' -> use 3rd column (index 2)
    - else -> use 2nd column (index 1)
- Writes a CSV at BASE_DIR/rmsd_summary.csv with columns:
    technique,molecule,min_rmsd,max_rmsd,count,source
"""

import csv
from pathlib import Path
import sys
import math

BASE_DIR = Path("/Users/jhonatan/Downloads/casp-predictions")
OUT_FILE = BASE_DIR / "rmsd_summary.csv"

technique_dirs = [p for p in BASE_DIR.iterdir() if p.is_dir() and p.name.endswith("_GARN")]
technique_dirs.sort()

rows = []

for tech_dir in technique_dirs:
    technique = tech_dir.name
    for mol_dir in sorted([d for d in tech_dir.iterdir() if d.is_dir()]):
        mol = mol_dir.name
        # find any *_rmsd.csv inside this mol_dir
        rmsd_files = sorted(mol_dir.glob("*_rmsd.csv"))
        if not rmsd_files:
            # maybe file named like {mol}_rmsd.csv directly under tech_dir
            alt = tech_dir / f"{mol}_rmsd.csv"
            if alt.exists():
                rmsd_files = [alt]
        if not rmsd_files:
            rows.append((technique, mol, "", "", 0, ""))
            continue
        # choose first rmsd file
        rmsd_file = rmsd_files[0]
        # Parse RMSD file format: path;rmsd_value; (semicolon-separated)
        values = []
        try:
            with rmsd_file.open() as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(';')
                    # Format: filename;rmsd_value;...
                    if len(parts) >= 2:
                        val = parts[1].strip()
                        try:
                            f = float(val)
                            if math.isfinite(f):
                                values.append(f)
                        except Exception:
                            continue
        except Exception as e:
            rows.append((technique, mol, "", "", 0, str(rmsd_file)))
            continue

        if values:
            mn = min(values)
            mx = max(values)
            cnt = len(values)
            rows.append((technique, mol, f"{mn:.6f}", f"{mx:.6f}", cnt, str(rmsd_file.relative_to(BASE_DIR))))
        else:
            rows.append((technique, mol, "", "", 0, str(rmsd_file.relative_to(BASE_DIR))))

# write output
with OUT_FILE.open("w", newline='') as out:
    writer = csv.writer(out)
    writer.writerow(["technique", "molecule", "min_rmsd", "max_rmsd", "count", "source"])
    for r in rows:
        writer.writerow(r)

print(f"Wrote summary to: {OUT_FILE}")
print("Rows:", len(rows))
