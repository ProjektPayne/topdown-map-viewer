"""Example plugin: builds a catalog of seeded random ponds on the fly, with no map files on disk.

    python tools/serve.py --plugin examples/plugin_random_ponds.py
    python tools/bundle.py --plugin examples/plugin_random_ponds.py -o ponds.html

A plugin is how a project plugs its own data in: read whatever your engine or generator writes, convert it to the
generic map format here, and the viewer, the live server and the one-file export all work unchanged.
"""
import json, math, random, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent   # relative paths in the catalog start here
SEEDS = range(1, 9)


def pond(seed):
    rnd = random.Random(seed)
    rx, ry = rnd.uniform(25, 45), rnd.uniform(18, 35)
    ph = [rnd.uniform(0, 6.28) for _ in range(3)]
    ring = []
    for i in range(36):
        a = 2 * math.pi * i / 36
        r = 1 + 0.15 * math.sin(2 * a + ph[0]) + 0.1 * math.sin(3 * a + ph[1]) + 0.05 * math.sin(5 * a + ph[2])
        ring.append([round(rx * r * math.cos(a), 1), round(ry * r * math.sin(a), 1)])
    trees = []
    while len(trees) < 40:
        a, d = rnd.uniform(0, 2 * math.pi), rnd.uniform(1.25, 1.9)
        trees.append({'shape': rnd.choice(['tree', 'tree', 'bush']), 'pos': [round(rx * d * math.cos(a), 1), round(ry * d * math.sin(a), 1)],
                      'scale': round(rnd.uniform(0.8, 1.3), 2)})
    return {'format': 'topdown-map/1', 'id': f'pond-{seed}', 'name': f'Pond seed {seed}', 'bounds': [-80, 80, -65, 65],
            'areas': [{'polygon': ring, 'style': 'water', 'label': f'Pond {seed}'}],
            'objects': trees,
            'markers': [{'pos': [0, -ry * 1.5], 'label': 'Spawn'}],
            'stats': {'radius_m': round((rx + ry) / 2, 1)}}


def catalog():
    return {'title': 'Random ponds (plugin example)',
            'columns': [{'key': 'radius_m', 'label': 'Radius', 'unit': 'm', 'digits': 1, 'better': 'high'}],
            'maps': [{'id': f'pond-{s}', 'name': f'Seed {s}', 'group': 'Generated', 'file': f'generated/pond-{s}.json',
                      'stats': pond(s)['stats']} for s in SEEDS]}


def read(path):
    m = re.fullmatch(r'generated/pond-(\d+)\.json', path)
    return json.dumps(pond(int(m.group(1)))).encode('utf-8') if m else None
