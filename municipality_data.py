"""Runtime lookup from the bundled dataset; the workbook is only read at build time."""
import json
from functools import lru_cache
from pathlib import Path

MUNICIPALITY_ERROR = 'Seleziona un comune dall’elenco.'


@lru_cache(maxsize=1)
def municipalities_by_code():
    path = Path(__file__).resolve().parent / '_static/global/istat_comuni.json'
    return {row['istat_code']: row for row in json.loads(path.read_text(encoding='utf-8'))}


def valid_municipality(name, code):
    row = municipalities_by_code().get(code)
    return row is not None and row['name'] == name
