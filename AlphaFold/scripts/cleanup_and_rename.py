#!/usr/bin/env python3
"""Delete all files except '*_model_0.pdb' in each directory and rename that file to the molecule name.

Example: fold_7yr6_2025_12_28_17_39_model_0.pdb -> 7YR6.pdb

Usage: python scripts/cleanup_and_rename.py /path/to/workspace
"""
import os
import sys
import re
import argparse
from fnmatch import fnmatch


def extract_id_from_name(name):
    m = re.search(r'fold_([A-Za-z0-9]+)', name)
    if m:
        return m.group(1).upper()
    # fallback: if directory starts with Xxxx_...
    m2 = re.match(r'([A-Za-z0-9]+)', name)
    if m2:
        return m2.group(1).upper()
    return None


def process_directory(dirpath, dry_run=False):
    entries = os.listdir(dirpath)
    model0_files = [f for f in entries if fnmatch(f, '*_model_0.pdb') and os.path.isfile(os.path.join(dirpath, f))]
    if not model0_files:
        return None

    # choose the first model_0 file if multiple
    model0 = model0_files[0]

    # determine molecule id from filename first, then directory name
    mol_id = extract_id_from_name(model0)
    if not mol_id:
        mol_id = extract_id_from_name(os.path.basename(dirpath))
    if not mol_id:
        # fallback to name before first underscore in model file name
        mol_id = model0.split('_')[1].upper() if '_' in model0 else os.path.splitext(model0)[0].upper()

    dest_name = f"{mol_id}.pdb"
    dest_path = os.path.join(dirpath, dest_name)
    model0_path = os.path.join(dirpath, model0)

    # Delete other files in this directory (not directories)
    deleted = []
    kept = []
    for entry in entries:
        full = os.path.join(dirpath, entry)
        if os.path.isfile(full):
            if entry == model0:
                kept.append(entry)
                continue
            # skip if it's already the destination name
            if entry == dest_name:
                # will be overwritten later
                try:
                    if not dry_run:
                        os.remove(full)
                except Exception:
                    pass
                deleted.append(entry)
                continue
            # remove any other file
            try:
                if not dry_run:
                    os.remove(full)
                deleted.append(entry)
            except Exception:
                pass

    # Rename model0 to destination (overwrite if exists)
    try:
        if not dry_run:
            if os.path.exists(dest_path):
                os.remove(dest_path)
            os.rename(model0_path, dest_path)
    except Exception as e:
        return {'dir': dirpath, 'error': str(e), 'deleted': deleted, 'kept': kept}

    return {'dir': dirpath, 'deleted': deleted, 'kept': [dest_name]}


def main(root, dry_run=False):
    results = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Only consider directories that contain a model_0 file at this level
        has_model0 = any(fnmatch(f, '*_model_0.pdb') for f in filenames)
        if has_model0:
            res = process_directory(dirpath, dry_run=dry_run)
            if res:
                results.append(res)

    # print summary
    for r in results:
        if 'error' in r:
            print('ERROR in', r['dir'], r['error'])
        else:
            print('Processed:', r['dir'])
            print('  Deleted:', len(r['deleted']))
            if r['deleted']:
                for d in r['deleted']:
                    print('   -', d)
            print('  Kept:', ', '.join(r['kept']))

    print('Done. Processed', len(results), 'folders.')
    return 0


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Cleanup directories keeping only model_0.pdb and renaming it')
    p.add_argument('root', nargs='?', default='.', help='Root directory to process')
    p.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    args = p.parse_args()
    sys.exit(main(args.root, dry_run=args.dry_run))
