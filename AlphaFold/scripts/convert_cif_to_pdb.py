#!/usr/bin/env python3
"""Convert all .cif files under a directory tree to .pdb using Biopython.

Usage: python scripts/convert_cif_to_pdb.py /path/to/workspace
"""
import os
import sys
import argparse

from Bio.PDB import MMCIFParser, PDBIO


def convert_file(infile, outfile):
    parser = MMCIFParser(QUIET=True)
    structure_id = os.path.splitext(os.path.basename(infile))[0]
    structure = parser.get_structure(structure_id, infile)
    io = PDBIO()
    io.set_structure(structure)
    io.save(outfile)


def main(root, overwrite=False):
    cif_paths = []
    for dirpath, dirs, files in os.walk(root):
        for f in files:
            if f.lower().endswith('.cif'):
                cif_paths.append(os.path.join(dirpath, f))

    if not cif_paths:
        print('No .cif files found under', root)
        return 0

    print(f'Found {len(cif_paths)} .cif file(s). Converting...')
    failures = []
    converted = 0
    for cif in cif_paths:
        pdb = os.path.splitext(cif)[0] + '.pdb'
        try:
            if os.path.exists(pdb) and not overwrite:
                print('Skipping (exists):', pdb)
                continue
            convert_file(cif, pdb)
            print('Wrote:', pdb)
            converted += 1
        except Exception as e:
            print('Failed:', cif, '->', e)
            failures.append((cif, str(e)))

    print(f'Converted: {converted}, Failed: {len(failures)}')
    if failures:
        print('Failures:')
        for f, err in failures:
            print('-', f, ':', err)
    return 0


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Convert .cif to .pdb recursively')
    p.add_argument('root', nargs='?', default='.', help='Root directory to scan')
    p.add_argument('--overwrite', action='store_true', help='Overwrite existing .pdb files')
    args = p.parse_args()
    sys.exit(main(args.root, args.overwrite))
