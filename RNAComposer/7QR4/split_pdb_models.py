#!/usr/bin/env python3
import sys
from pathlib import Path

p = Path(__file__).parent / '7QR4.pdb'
if len(sys.argv) > 1:
    p = Path(sys.argv[1])

if not p.exists():
    print(f"File not found: {p}")
    sys.exit(2)

prefix = p.stem
out_dir = p.parent

with p.open('r') as f:
    model_lines = []
    model_idx = 0
    in_model = False
    for line in f:
        if line.startswith('MODEL'):
            in_model = True
            model_lines = [line]
            # try to parse index
            try:
                model_idx = int(line.split()[1])
            except Exception:
                model_idx += 1
        elif line.startswith('ENDMDL') and in_model:
            model_lines.append(line)
            out_path = out_dir / f"{prefix}_model_{model_idx}.pdb"
            with out_path.open('w') as out:
                out.writelines(model_lines)
            print(f"Wrote: {out_path}")
            in_model = False
            model_lines = []
        elif in_model:
            model_lines.append(line)
    # handle trailing model without ENDMDL
    if in_model and model_lines:
        model_idx = model_idx or 1
        out_path = out_dir / f"{prefix}_model_{model_idx}.pdb"
        with out_path.open('w') as out:
            out.writelines(model_lines)
        print(f"Wrote (no ENDMDL): {out_path}")

print('Done')
