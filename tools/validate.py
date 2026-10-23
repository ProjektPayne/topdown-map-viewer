"""Check map and catalog files against the schemas in schema/.

    python tools/validate.py examples/catalog.json examples/maps/*.json

Needs the jsonschema package (pip install jsonschema). A file with a "maps" list is checked as a catalog, and the map
files it names are checked too.
"""
import json, sys
from pathlib import Path

SCHEMA = Path(__file__).resolve().parents[1] / 'schema'


def main(paths):
    try:
        import jsonschema
        from referencing import Registry, Resource
    except ImportError:
        sys.exit('validate.py needs jsonschema 4.18 or newer: pip install jsonschema')
    schemas = {n: json.loads((SCHEMA / n).read_text(encoding='utf-8')) for n in ('map.schema.json', 'catalog.schema.json')}
    registry = Registry().with_resources([(n, Resource.from_contents(s)) for n, s in schemas.items()]
                                         + [(s['$id'], Resource.from_contents(s)) for s in schemas.values()])
    check = {n: jsonschema.Draft202012Validator(s, registry=registry) for n, s in schemas.items()}
    todo, seen, bad = [Path(p) for p in paths], set(), 0
    while todo:
        p = todo.pop(0).resolve()
        if p in seen:
            continue
        seen.add(p)
        data = json.loads(p.read_text(encoding='utf-8'))
        kind = 'catalog.schema.json' if isinstance(data.get('maps'), list) else 'map.schema.json'
        errors = sorted(check[kind].iter_errors(data), key=lambda e: list(e.absolute_path))
        for e in errors:
            print(f'{p}: {"/".join(map(str, e.absolute_path)) or "(root)"}: {e.message}')
        bad += bool(errors)
        if kind == 'catalog.schema.json':
            for m in data['maps']:
                for v in [m, *(m.get('versions') or [])]:
                    if v.get('file'):
                        todo.append(p.parent / v['file'])
        print(f'{"FAIL" if errors else "ok  "} {p.name} ({kind.split(".")[0]})')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main(sys.argv[1:] or ['examples/catalog.json'])
