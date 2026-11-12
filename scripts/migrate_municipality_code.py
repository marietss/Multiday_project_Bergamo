"""Add the nullable municipality code to an existing SQLite oTree database.

Run with the study server stopped: python3 scripts/migrate_municipality_code.py db.sqlite3
Existing names are never backfilled or changed. Fresh databases use the model.
For an existing PostgreSQL deployment, apply the equivalent additive migration:
ALTER TABLE intro_player ADD COLUMN IF NOT EXISTS current_municipality_istat_code VARCHAR(10000);
"""
import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('database', type=Path)
    args = parser.parse_args()
    path = args.database.resolve(strict=True)
    with sqlite3.connect(str(path)) as connection:
        columns = {row[1] for row in connection.execute('PRAGMA table_info(intro_player)')}
        if not columns:
            raise RuntimeError('No intro_player table; use normal oTree initialization for a fresh database.')
        if 'current_municipality_istat_code' in columns:
            print('Column already exists; nothing changed.')
        else:
            backup = path.with_name(path.name + '.before-municipality-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.bak')
            with sqlite3.connect(str(backup)) as destination:
                connection.backup(destination)
            connection.execute('ALTER TABLE intro_player ADD COLUMN current_municipality_istat_code VARCHAR(10000)')
            print(f'Added nullable code column; backup: {backup}')
