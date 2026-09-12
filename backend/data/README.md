# India postal directory

Source: [GeoNames India postal extract](https://download.geonames.org/export/zip/IN.zip), attributed to [GeoNames](https://www.geonames.org/).

Licensed under CC BY 4.0, per the publisher's [postal data readme](https://download.geonames.org/export/zip/readme.txt). Normalized from the India tab-delimited extract to a compressed CSV of pincode, district, state and locality. See `postal-source.json` for download time, counts and source archive checksum.

This is reference data, not an India Post certification or a guarantee of current completeness. Multiple localities share a pincode. Historical administrative names can occur; confirm destination details with the courier.

Postal import never creates enabled delivery coverage. The owner must approve delivery separately. Refresh with `python infra/postal/refresh.py`; apply a new snapshot explicitly with `flask --app backend import-postal-directory backend/data/india-postal.csv.gz --source https://download.geonames.org/export/zip/IN.zip`.
