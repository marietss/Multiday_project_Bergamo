"""Add occupation to an existing SQLite database, preserving all legacy data.

Stop the study server before running:
python3 scripts/migrate_occupation_category.py db.sqlite3

Fresh databases use the oTree model. PostgreSQL equivalent for existing deployments:
ALTER TABLE intro_player ADD COLUMN IF NOT EXISTS occupation_category VARCHAR(10000);
No education or employment values are remapped.
"""
import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def migrate(path):
    path = Path(path).resolve(strict=True)
    with sqlite3.connect(str(path)) as connection:
        columns = {row[1] for row in connection.execute('PRAGMA table_info(intro_player)')}
        if not columns:
            raise RuntimeError('No intro_player table; initialize fresh databases through oTree.')
        if 'occupation_category' in columns:
            print('occupation_category already exists; nothing changed.')
            return
        backup = path.with_name(path.name + '.before-occupation-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.bak')
        with sqlite3.connect(str(backup)) as destination:
            connection.backup(destination)
        connection.execute('ALTER TABLE intro_player ADD COLUMN occupation_category VARCHAR(10000)')
        print(f'Added nullable occupation_category; backup: {backup}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('database')
    migrate(parser.parse_args().database)
