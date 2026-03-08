import json
from shapely.geometry import shape

def calc(p1, p2):
    with open(p1, encoding='utf-8') as f:
        data = json.load(f)
    print(f"--- {p2} ---")
    for feat in data['features']:
        name = feat['properties'].get('DistName') or feat['properties'].get('name') or feat['properties'].get('NAME')
        geom = shape(feat['geometry'])
        c = geom.centroid
        print(f'    {{"name": "{name}", "lng": {c.x:.4f}, "lat": {c.y:.4f}}},')

calc('data/yiyang_townships.geojson', 'YIYANG')
calc('data/wannian_townships.geojson', 'WANNIAN')
