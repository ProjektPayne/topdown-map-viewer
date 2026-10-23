"""Export the viewer and a catalog as one self-contained HTML file that opens with a double-click (no server, no internet).

    python tools/bundle.py examples/catalog.json -o maps.html
    python tools/bundle.py --plugin my_project_plugin.py -o maps.html

Embeds three.js, the viewer, the catalog and every map and mesh file it names (gzip + base64).
"""
import argparse, base64, gzip, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mapviewer_common import VIEWER, Source, referenced_files  # noqa: E402

THREE_TAG = '<script src="vendor/three-r181.min.js"></script>'


def build(source):
    cat = source.catalog()
    if not cat.get('maps'):
        raise SystemExit('The catalog lists no maps.')
    files = {p: base64.b64encode(gzip.compress(data, 9, mtime=0)).decode('ascii')
             for p, data in referenced_files(source, cat).items()}
    bundle = {'catalog': cat, 'catalog_path': source.catalog_path, 'files': files}
    page = (VIEWER / 'index.html').read_text(encoding='utf-8')
    if THREE_TAG not in page:
        raise SystemExit('viewer/index.html no longer loads vendor/three-r181.min.js; update tools/bundle.py')
    three = (VIEWER / 'vendor' / 'three-r181.min.js').read_text(encoding='utf-8').replace('</script', '<\\/script')
    data = json.dumps(bundle, separators=(',', ':')).replace('</', '<\\/')
    return page.replace(THREE_TAG, f'<script>{three}</script>\n<script type="application/json" id="mv-bundle">{data}</script>'), len(cat['maps']), len(files)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('catalog', nargs='?')
    ap.add_argument('--plugin')
    ap.add_argument('-o', '--out', default='maps.html')
    a = ap.parse_args()
    page, maps, files = build(Source(a.catalog, a.plugin))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding='utf-8')
    print(f'{out}  ({out.stat().st_size / 1e6:.1f} MB, {maps} maps, {files} files)')


if __name__ == '__main__':
    main()
