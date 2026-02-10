#!/usr/bin/env python3
"""
Recursively find .pdb files under the given root (default: this script's parent)
and split each MODEL...ENDMDL block into separate files named
<basename>_model_<n>.pdb in the same directory as the source file.

Usage:
  python3 split_all_pdbs.py [root_dir]
"""
import sys
from pathlib import Path

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent

pdb_paths = list(root.rglob('*.pdb'))
if not pdb_paths:
    print(f"No .pdb files found under {root}")
    sys.exit(0)

skipped = 0
processed = 0
for p in pdb_paths:
    # skip already-split files
    if p.name.endswith('.pdb') and '_model_' in p.stem:
        skipped += 1
        continue
    try:
        with p.open('r') as f:
            in_model = False
            model_lines = []
            model_idx = 0
            wrote = 0
            for line in f:
                if line.startswith('MODEL'):
                    in_model = True
                    model_lines = [line]
                    # parse index if present
                    parts = line.split()
                    try:
                        model_idx = int(parts[1])
                    except Exception:
                        model_idx += 1
                elif line.startswith('ENDMDL') and in_model:
                    model_lines.append(line)
                    out_path = p.parent / f"{p.stem}_model_{model_idx}.pdb"
                    with out_path.open('w') as out:
                        out.writelines(model_lines)
                    print(f"Wrote: {out_path}")
                    wrote += 1
                    in_model = False
                    model_lines = []
                elif in_model:
                    model_lines.append(line)
            # trailing model without ENDMDL
            if in_model and model_lines:
                model_idx = model_idx or 1
                out_path = p.parent / f"{p.stem}_model_{model_idx}.pdb"
                with out_path.open('w') as out:
                    out.writelines(model_lines)
                print(f"Wrote (no ENDMDL): {out_path}")
                wrote += 1
        if wrote:
            processed += 1
        else:
            # no MODEL/ENDMDL found, skip
            pass
    except Exception as e:
        print(f"Error processing {p}: {e}")

print('\nSummary:')
print(f'  total .pdb files found: {len(pdb_paths)}')
print(f'  processed (had models): {processed}')
print(f'  skipped (already split): {skipped}')
print('Done')
