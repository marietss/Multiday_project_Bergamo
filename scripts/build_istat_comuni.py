"""Deterministically extract the authoritative XLSX, without runtime Excel dependencies.

Run from any directory: python3 scripts/build_istat_comuni.py [--check]
--check compares every generated record with the source without writing files.
"""
import argparse
import json
import posixpath
import re
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/istat/comuni_istat_2026-10-16.xlsx'
OUTPUT = ROOT / '_static/global/istat_comuni.json'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def source_records():
    with zipfile.ZipFile(SOURCE) as archive:
        strings = [
            ''.join(t.text or '' for t in item.findall('.//s:t', NS))
            for item in ET.fromstring(archive.read('xl/sharedStrings.xml'))
        ]
        sheets = ET.fromstring(archive.read('xl/workbook.xml'))
        sheet = next(s for s in sheets.findall('s:sheets/s:sheet', NS)
                     if s.get('name') == 'Codici statistici e denominazio')
        rel_id = sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        rels = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        target = next(r.get('Target') for r in rels if r.get('Id') == rel_id)
        path = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
        rows = ET.fromstring(archive.read(path)).findall('s:sheetData/s:row', NS)
        decoded = []
        for row in rows:
            values = {}
            for cell in row:
                col = re.match(r'[A-Z]+', cell.get('r')).group()
                value = cell.find('s:v', NS)
                text = value.text if value is not None else ''
                if cell.get('t') == 's':
                    text = strings[int(text)]
                elif cell.get('t') == 'inlineStr':
                    text = ''.join(t.text or '' for t in cell.findall('.//s:t', NS))
                values[col] = text
            decoded.append(values)
    headers = {value: col for col, value in decoded[0].items()}
    columns = {
        'name': 'Comune', 'istat_code': 'Codice Comune (alfanumerico)',
        'province_abbreviation': 'Sigla automobilistica',
    }
    return [{key: row.get(headers[column], '') for key, column in columns.items()}
            for row in decoded[1:]]


def validate(records):
    missing = {key: sum(not row[key] for row in records)
               for key in ['name', 'istat_code', 'province_abbreviation']}
    codes = Counter(row['istat_code'] for row in records)
    duplicates = [code for code, count in codes.items() if count > 1]
    malformed = [r for r in records if not re.fullmatch(r'[0-9]{6}', r['istat_code'])]
    print(json.dumps(dict(source_rows=len(records), unique_codes=len(codes),
                          missing=missing, duplicate_codes=duplicates,
                          malformed_codes=len(malformed)), ensure_ascii=False))
    if len(records) != 7894 or any(missing.values()) or duplicates or malformed:
        raise ValueError('Source integrity check failed; no corrections or deduplication performed.')
    names = Counter(row['name'] for row in records)
    print('Repeated names:', json.dumps(
        [r for r in records if names[r['name']] > 1], ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    records = source_records()
    validate(records)
    content = json.dumps(records, ensure_ascii=False, separators=(',', ':')) + '\n'
    if args.check:
        assert OUTPUT.read_text(encoding='utf-8') == content, 'Generated data differs from XLSX'
    else:
        OUTPUT.write_text(content, encoding='utf-8')
    print(f'Generated records: {len(records)}; every name/code/province matches the source.')
