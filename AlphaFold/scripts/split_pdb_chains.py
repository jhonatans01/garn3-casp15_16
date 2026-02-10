#!/usr/bin/env python3
"""Split PDB files into one file per chain.

Usage: python scripts/split_pdb_chains.py /path/to/workspace

For each .pdb found, writes files named <base>_<chain>.pdb (e.g. 7YR6_A.pdb).
Keeps the original file.
"""
import os
import sys
import argparse

from Bio.PDB import PDBParser, PDBIO, Select


class ChainSelect(Select):
    def __init__(self, chain_id):
        self.chain_id = chain_id

    def accept_chain(self, chain):
        return chain.get_id() == self.chain_id


def split_pdb(pdb_path, out_dir=None, overwrite=False):
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure(os.path.basename(pdb_path), pdb_path)
    chains = list(structure.get_chains())
    if not chains:
        return {'file': pdb_path, 'chains': 0}

    base = os.path.splitext(os.path.basename(pdb_path))[0]
    if out_dir is None:
        out_dir = os.path.dirname(pdb_path)

    io = PDBIO()
    written = []
    for chain in chains:
        cid = chain.get_id()
        # normalize chain id
        if cid == ' ' or cid == '' or cid is None:
            cid_label = 'UNK'
        else:
            cid_label = str(cid)

        out_name = f"{base}_{cid_label}.pdb"
        out_path = os.path.join(out_dir, out_name)
        if os.path.exists(out_path) and not overwrite:
            written.append(out_path)
            continue

        io.set_structure(structure)
        sel = ChainSelect(chain.get_id())
        io.save(out_path, select=sel)
        written.append(out_path)

    return {'file': pdb_path, 'chains': len(chains), 'written': written}


def main(root, overwrite=False):
    results = []
    for dirpath, dirnames, filenames in os.walk(root):
        for f in filenames:
            if f.lower().endswith('.pdb'):
                # skip per-chain files if they already follow base_CHAIN.pdb pattern
                if '_' in f and len(f.split('_')[-1].split('.')[0]) <= 2 and f.split('_')[-1].split('.')[0].isalnum():
                    # This might be a chain file; skip to avoid duplicating
                    continue
                pdb_path = os.path.join(dirpath, f)
                try:
                    res = split_pdb(pdb_path, out_dir=dirpath, overwrite=overwrite)
                    results.append(res)
                    print(f"Split {pdb_path}: {res.get('chains',0)} chain(s)")
                except Exception as e:
                    print(f"Failed to split {pdb_path}: {e}")

    print(f"Done. Processed {len(results)} PDB files.")
    return 0


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Split PDB files into per-chain PDBs')
    p.add_argument('root', nargs='?', default='.', help='Root directory to scan')
    p.add_argument('--overwrite', action='store_true', help='Overwrite existing chain files')
    args = p.parse_args()
    sys.exit(main(args.root, overwrite=args.overwrite))
