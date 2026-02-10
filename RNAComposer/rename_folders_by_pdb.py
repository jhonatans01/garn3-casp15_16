#!/usr/bin/env python3
import re
from pathlib import Path

root = Path(__file__).parent

pattern_candidates = ['*.pdb', '*-log.txt', '*.pdb-blocks.txt']
renamed = []
skipped = []

for d in sorted(root.iterdir()):
    if not d.is_dir():
        continue
    if not d.name.startswith('rnacomposer-'):
        continue
    pdb_id = None
    # find candidate files
    for pat in pattern_candidates:
        try:
            for f in d.glob(pat):
                stem = f.name.split('.')[0]
                # handle names like "7QR4-log" or "7QR4.pdb"
                m = re.match(r'^([A-Za-z0-9]{4,6})', stem)
                if m:
                    pdb_id = m.group(1)
                    break
        except Exception:
            pass
        if pdb_id:
            break
    if not pdb_id:
        skipped.append((d.name, 'no id found'))
        continue
    target = root / pdb_id
    # avoid renaming to an existing folder; if exists, append suffix
    if target.exists():
        if target.samefile(d):
            skipped.append((d.name, f'already named {pdb_id}'))
            continue
        # find unique name
        n = 2
        while True:
            candidate = root / f"{pdb_id}_{n}"
            if not candidate.exists():
                target = candidate
                break
            n += 1
    try:
        d.rename(target)
        renamed.append((d.name, target.name))
    except Exception as e:
        skipped.append((d.name, f'error: {e}'))

print('Renamed:')
for a,b in renamed:
    print(f'  {a} -> {b}')
print('\nSkipped:')
for a,reason in skipped:
    print(f'  {a}: {reason}')

print('\nDone')
