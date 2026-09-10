"""Build the Expo website and a source ZIP for Azure's Linux Python build."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from urllib.parse import urlsplit
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--api-url', required=True, help='Deployed HTTPS API URL ending in /api/v1')
parser.add_argument('--mobile-dir', type=Path, default=root / 'mobile', help='Folder with installed Expo dependencies')
args = parser.parse_args()
url = urlsplit(args.api_url)
if url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment or url.path.rstrip('/') != '/api/v1':
    parser.error('Use an HTTPS API URL ending in /api/v1, without credentials, query or fragment.')
mobile = args.mobile_dir.resolve()
cli = mobile / 'node_modules/expo/bin/cli'
if not cli.is_file():
    parser.error('Run npm ci inside mobile first.')
build = root / '.azure-build'
build.mkdir(exist_ok=True)
target = build / 'app.zip'
with tempfile.TemporaryDirectory(prefix='web-', dir=build, ignore_cleanup_errors=True) as temporary:
    stage = Path(temporary).resolve()
    assert stage.parent == build.resolve()
    env = {**os.environ, 'EXPO_PUBLIC_API_URL': args.api_url.rstrip('/'), 'CI': '1'}
    subprocess.run(['node', '--dns-result-order=ipv4first', str(cli), 'export', '--platform', 'web', '--output-dir', str(stage / 'web')], cwd=mobile, env=env, check=True)
    shutil.copytree(root / 'backend', stage / 'backend', ignore=shutil.ignore_patterns('__pycache__', 'tests', '*.pyc', '*.log', '.env*'))
    shutil.copytree(root / 'mobile/assets/catalog', stage / 'mobile/assets/catalog')
    (stage / 'infra/azure').mkdir(parents=True)
    for name in ['requirements.txt', 'wsgi.py', 'infra/azure/start.sh']:
        shutil.copyfile(root / name, stage / name)
    with ZipFile(target, 'w', ZIP_DEFLATED) as archive:
        for path in sorted(stage.rglob('*')):
            if path.is_file(): archive.write(path, path.relative_to(stage).as_posix())
with ZipFile(target) as archive:
    assert archive.testzip() is None
    for name in ['web/index.html', 'backend/web.py', 'wsgi.py', 'requirements.txt', 'infra/azure/start.sh']:
        assert name in archive.namelist(), name
print(f'Azure ZIP ready: {target} ({target.stat().st_size:,} bytes). No upload performed.')
