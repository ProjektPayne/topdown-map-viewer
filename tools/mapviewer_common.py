"""Shared helpers for serve.py and bundle.py: loading a plugin and reading the files a catalog names."""
import importlib.util, json, posixpath
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
VIEWER = PACKAGE / 'viewer'


class Source:
    """Where a catalog and its files come from: a catalog file on disk, or a plugin.

    A plugin is a Python file with:
        ROOT            the folder the catalog's relative paths start from (a str or Path)
        catalog()       returns the catalog as a dict (built fresh on each call, so new maps show up on a refresh)
        read(path)      optional: bytes for a ROOT-relative path that is not a real file (converted on the fly), else None
    The catalog is then served as catalog.json at ROOT.
    """

    def __init__(self, catalog=None, plugin=None):
        if bool(catalog) == bool(plugin):
            raise SystemExit('Give a catalog file or --plugin, not both.')
        self.plugin = None
        if plugin:
            spec = importlib.util.spec_from_file_location('mapviewer_plugin', plugin)
            self.plugin = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.plugin)
            self.root = Path(self.plugin.ROOT).resolve()
            self.catalog_path = 'catalog.json'
        else:
            path = Path(catalog).resolve()
            if not path.is_file():
                raise SystemExit(f'Catalog not found: {catalog}')
            self.root = path.parent
            self.catalog_path = path.name

    def catalog(self):
        if self.plugin:
            return self.plugin.catalog()
        return json.loads((self.root / self.catalog_path).read_text(encoding='utf-8'))

    def read(self, rel):
        """Bytes of a ROOT-relative path (plugin first, then disk), or None. Never reads outside ROOT."""
        rel = rel.lstrip('/')
        if rel == self.catalog_path:
            return json.dumps(self.catalog()).encode('utf-8')
        if self.plugin and hasattr(self.plugin, 'read'):
            data = self.plugin.read(rel)
            if data is not None:
                return data
        p = (self.root / rel).resolve()
        return p.read_bytes() if p.is_file() and self.root in p.parents else None


def join(base, ref):
    """Resolve ref against the file base, the same way the viewer does in a bundle (URL rules, no escaping the root)."""
    if '://' in ref:
        return None  # remote files are left to the browser
    parts = []
    for seg in posixpath.join(posixpath.dirname(base), ref).split('/'):
        if seg == '..':
            if parts:
                parts.pop()
        elif seg not in ('', '.'):
            parts.append(seg)
    return '/'.join(parts)


def referenced_files(source, cat):
    """Every ROOT-relative file the catalog's maps need: map files, then the meshes each map names."""
    files = {}

    def add_map(map_obj, base):
        for m in (map_obj or {}).get('meshes') or []:
            p = join(base, m['url'])
            if p and p not in files:
                files[p] = None

    for e in cat.get('maps') or []:
        for v in [e, *(e.get('versions') or [])]:
            if v.get('map'):
                add_map(v['map'], source.catalog_path)
            if v.get('file'):
                p = join(source.catalog_path, v['file'])
                if p is None:
                    continue
                data = source.read(p)
                if data is None:
                    raise SystemExit(f'Missing map file: {p}')
                files[p] = data
                add_map(json.loads(data), p)
    for p, data in files.items():
        if data is None:
            files[p] = source.read(p)
            if files[p] is None:
                raise SystemExit(f'Missing mesh file: {p}')
    return files
