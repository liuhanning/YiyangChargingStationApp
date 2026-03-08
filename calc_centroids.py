import json
try:
    from shapely.geometry import shape
except ImportError:
    import sys
    sys.exit("shapely not installed")

with open('data/yiyang_townships.geojson', encoding='utf-8') as f:
    data = json.load(f)

print("TOWNSHIP_LABELS = [")
for feat in data['features']:
    name = feat['properties'].get('DistName') or feat['properties'].get('name') or feat['properties'].get('NAME')
    geom = shape(feat['geometry'])
    centroid = geom.centroid
    print(f'    {{"name": "{name}", "lng": {centroid.x:.4f}, "lat": {centroid.y:.4f}}},')
print("]")
