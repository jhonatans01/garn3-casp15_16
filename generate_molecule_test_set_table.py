#!/usr/bin/env python3
"""
Generate test set table with molecule descriptions, nucleotides, and player counts.
"""
from pathlib import Path
import pandas as pd

BASE = Path('.').resolve()
DESC_FILE = BASE / 'molecule_descriptions.csv'
MOL_SIZES_FILE = BASE / 'mol_sizes.csv'
REFERENCE_DIR = BASE / 'REFERENCE_PBD'
OUTPUT_FILE = BASE / 'molecule_test_set_table.tex'

# Read descriptions from CSV
desc_df = pd.read_csv(DESC_FILE)
molecules_data = []
for _, row in desc_df.iterrows():
    molecules_data.append((
        row['CASP'],
        str(row['Target_ID']),
        row['Molecule'],
        row['Description']
    ))

# Read mol_sizes.csv for nucleotide counts
mol_sizes_df = pd.read_csv(MOL_SIZES_FILE, sep=';')
mol_sizes_dict = dict(zip(mol_sizes_df['mol'], mol_sizes_df['length']))

# Read player counts from REFERENCE_PBD GARN files
player_counts = {}
for mol in [m[2] for m in molecules_data]:
    garn_file = REFERENCE_DIR / mol / f"{mol}_GARN.csv"
    if garn_file.exists():
        with open(garn_file, 'r') as f:
            first_line = f.readline().strip()
            # First line contains player count followed by semicolon
            player_counts[mol] = first_line.rstrip(';')
    else:
        player_counts[mol] = '–'

# Build LaTeX table
latex_lines = [
    r"\begin{table}[!ht]",
    r"\begin{adjustwidth}{-2.5in}{0in}",
    r"\centering",
    r"\caption{{\bf Test set}. Molecules used to run the simulations. This test set contains " + str(len(molecules_data)) + r" molecules.}",
    r"\begin{tabular}{llllll}",
    r"\toprule",
    r"\textbf{CASP} & \textbf{Target ID} & \textbf{Molecule} & \textbf{Description} & \textbf{Nucleotides} & \textbf{Players} \\",
    r"\midrule",
]

# Add data rows
for casp, casp_id, mol, desc in molecules_data:
    # Get nucleotide count from mol_sizes
    nucleotides = mol_sizes_dict.get(mol, '–')
    # Get player count from REFERENCE_PBD
    players = player_counts.get(mol, '–')
    
    latex_lines.append(
        f"{casp} & {casp_id} & {mol} & {desc} & {nucleotides} & {players} \\\\"
    )
    latex_lines.append(r"\hline")

# Remove last \hline
latex_lines.pop()
latex_lines.append(r"\bottomrule")
latex_lines.append(r"\end{tabular}")
latex_lines.append(r"\end{adjustwidth}")
latex_lines.append(r"\end{table}")

# Write to file
with OUTPUT_FILE.open('w') as fh:
    fh.write('\n'.join(latex_lines))

print(f"✅ Test set table written to: {OUTPUT_FILE}")
print(f"Molecules: {len(molecules_data)}")
