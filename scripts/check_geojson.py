import json
from shapely.geometry import shape
with open('data/yiyang_townships.geojson', 'r', encoding='utf-8') as f:
    gj = json.load(f)
with open('out2.txt', 'w', encoding='utf-8') as fout:
    for feat in gj['features']:
        props = feat['properties']
        name = props.get('DistName', props.get('NAME', props.get('name', '')))
        geom = shape(feat['geometry'])
        fout.write(f'{name}: {geom.centroid.x:.3f}, {geom.centroid.y:.3f}\n')
