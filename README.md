# topdown-map-viewer

A small Three.js viewer for game level layouts. Describe a map as plain JSON (polygons, paths, stand-in shapes, markers and optional glTF meshes), list your maps in a catalog, and browse them in 3D with stats, layer toggles and PNG export. It can also export everything as **one HTML file** that anyone can double-click: no install, no server, no internet.

It started as the level-design viewer for the co-op fishing game *Trespass Fishin'* and was pulled out so other projects can use it.

![Example map](docs/example.png)

## Quick start

Needs Python 3.8+ and a browser. No other dependencies.

```
python tools/serve.py examples/catalog.json          # view the example maps in your browser
python tools/bundle.py examples/catalog.json -o maps.html   # export them as one shareable file
```

Inside the viewer: click a row or press the arrow keys to switch maps, drag to orbit, right-drag to pan, scroll to zoom. **Top view** and **3/4 view** reframe the camera, **Save PNG** saves what you see. **Fog** turns on a distance haze (off by default, remembered per browser). Hover over anything with a label to read it. You can also drop a map or catalog `.json` file (plus the files it names) onto the page.

## The map format

A map is one JSON file. Every list is optional, so a map can start as a single polygon. The full reference is [`schema/map.schema.json`](schema/map.schema.json).

```json
{
  "format": "topdown-map/1",
  "name": "Mill Pond",
  "units_per_meter": 1,
  "bounds": [-100, 100, -80, 80],
  "palette": { "spawn": { "color": "#ffcc33", "label": "Player spawn" } },
  "areas":   [{ "polygon": [[-50, -30], [50, -30], [40, 35], [-45, 30]], "style": "water", "label": "Mill Pond" }],
  "paths":   [{ "points": [[-100, -58], [0, -55], [100, -58]], "width": 6, "style": "road" }],
  "objects": [{ "shape": "tree", "pos": [60, 20] },
              { "shape": "box", "pos": [0, -41, 0.3], "size": [3, 14, 0.3], "style": "wood", "label": "Dock" }],
  "markers": [{ "pos": [0, -60], "style": "spawn", "label": "Spawn 1" }],
  "meshes":  [{ "url": "../meshes/cabin.gltf", "position": [71, 41, 0], "yaw": 20 }]
}
```

* **Coordinates**: x east, y north, z up. `units_per_meter` says how many map units make a metre: 1 for metres, 100 for Unreal centimetres. `yaw` is degrees counter-clockwise from +x seen from above.
* **areas**: filled polygons (with optional `holes`): ground, water, fields. Later areas draw on top.
* **paths**: lines with a `width`: roads, trails, rivers.
* **objects**: `box`, `cylinder`, `cone` and `sphere` are scaled to `size` `[x, y, height]`; `tree`, `bush` and `rock` have a natural size and are drawn instanced, so thousands are fine.
* **markers**: glowing `pin`, `arrow`, `flag` or `box` points for spawns, pickups and objectives.
* **meshes**: `.gltf` or `.glb` files (metres, +y up, north along -z, or set `"north_axis": "+z"`). They keep their own materials unless you give a `style` or `color`. A glTF node whose `extras.layer` is set follows that layer's checkbox.
* **recolor** on a mesh repaints parts of it by node name (a regular expression), optionally only where the material's extras carry a flag, such as materials an exporter could not read.
* **Styles and colours**: every element takes a `color`, or a `style` looked up in the map's `palette` and then in the built-in palette (ground, water, road, asphalt, path, sand, dirt, concrete, wood, stone, building, roof, hedge, tree, bush, rock, marker). Palette entries with a `label` make up the legend.
* **Layers**: each element goes on a layer (ground, water, roads, structures, props, markers, or any id you choose), and every layer gets a show/hide checkbox. List a layer under `layers` to rename it or hide it by default.

## Catalogs

A catalog lists the maps, groups them and adds stat columns. See [`schema/catalog.schema.json`](schema/catalog.schema.json) and [`examples/catalog.json`](examples/catalog.json).

```json
{
  "title": "My levels",
  "columns": [{ "key": "water_m2", "label": "Water", "unit": "m²", "better": "high" }],
  "maps": [
    { "id": "mill-pond", "name": "Mill Pond", "group": "Lakes", "file": "maps/mill-pond.json", "stats": { "water_m2": 6453 } },
    { "id": "camp", "name": "Riverside Camp", "group": "Rivers", "file": "maps/camp.json", "tags": ["draft"],
      "version_label": "Built", "versions": [{ "label": "Bridge draft", "file": "maps/camp-bridge.json" }] }
  ]
}
```

With `better` set, the best value in each group shows green and the worst red. `versions` adds a picker for alternatives of the same map, such as a design draft and what was actually built. A map can also sit inline in the catalog under `map` instead of `file`. `?select=<id>` in the URL opens a given map.

## Plugins: plugging in your own data

Most projects already have level data in their own shape: an engine export, a generator's output, a level editor's save files. Instead of writing converted files to disk, write a small Python plugin:

```python
ROOT = Path(__file__).parent        # relative paths in the catalog start here

def catalog():                       # called on every page load, so new maps show up on refresh
    return {"title": "My game", "maps": [{"id": "lvl1", "name": "Level 1", "file": "generated/lvl1.json"}]}

def read(path):                      # optional: bytes for paths that are not real files
    if path == "generated/lvl1.json":
        return json.dumps(convert(load_my_level("lvl1"))).encode()
    return None                      # anything else is read from ROOT
```

```
python tools/serve.py --plugin my_plugin.py
python tools/bundle.py --plugin my_plugin.py -o levels.html
```

[`examples/plugin_random_ponds.py`](examples/plugin_random_ponds.py) is a working example that generates seeded ponds on the fly.

## Checking files

```
pip install jsonschema
python tools/validate.py examples/catalog.json
```

A catalog is checked together with every map file it names.

## Opening the viewer without the server

`viewer/index.html` also takes `?map=<url>` or `?catalog=<url>` when it is served by any static web server. Opened straight from disk with no parameters, it waits for a file to be dropped on it.

## Layout

```
viewer/index.html           the viewer (one file, no build step)
viewer/vendor/              three.js r181 with OrbitControls and GLTFLoader, one classic script (MIT)
schema/                     JSON schemas for maps and catalogs
tools/serve.py              local server (localhost only)
tools/bundle.py             one-file HTML export
tools/validate.py           schema check
examples/                   sample catalog, maps, a glTF mesh and a plugin
```

## License

MIT, see [LICENSE](LICENSE). three.js is MIT licensed by the three.js authors.
