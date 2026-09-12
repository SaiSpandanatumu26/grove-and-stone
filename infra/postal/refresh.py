"""Refresh the licensed GeoNames India postal reference snapshot; not coverage."""
import csv
import gzip
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

SOURCE = 'https://download.geonames.org/export/zip/IN.zip'
root = Path(__file__).resolve().parents[2] / 'backend/data'
root.mkdir(exist_ok=True)
with urlopen(SOURCE, timeout=60) as response: archive = response.read(10_000_000)
rows = list(csv.reader(io.StringIO(ZipFile(io.BytesIO(archive)).read('IN.txt').decode('utf-8')), delimiter='\t'))
if len(rows) < 100000 or any(len(r) != 12 or r[0] != 'IN' or len(r[1]) != 6 or not r[1].isascii() or not r[1].isdigit() or not r[3] or not r[5] for r in rows):
    raise ValueError('Unexpected postal data; previous snapshot preserved')
with gzip.open(root / 'india-postal.csv.gz', 'wt', encoding='utf-8', newline='') as stream:
    writer = csv.writer(stream)
    writer.writerow(['pincode', 'district', 'state', 'office'])
    writer.writerows((r[1], r[5], r[3], r[2]) for r in rows)
metadata = dict(source=SOURCE, publisher='GeoNames', license='CC BY 4.0', attribution='https://www.geonames.org/',
                downloaded_at=datetime.now(timezone.utc).isoformat(), archive_sha256=hashlib.sha256(archive).hexdigest(),
                localities=len(rows), pincodes=len({r[1] for r in rows}), delivery_coverage=False)
(root / 'postal-source.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
print(f"Saved {metadata['pincodes']} postal codes and {metadata['localities']} locality records. Delivery coverage unchanged.")
