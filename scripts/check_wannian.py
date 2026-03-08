import json
from pathlib import Path

# read wannian_townships.geojson
data_dir = Path(r"c:\Users\lhn\OneDrive\Desktop\江西\弋阳充电桩项目\data")
with open(data_dir / "wannian_townships.geojson", "r", encoding="utf-8") as f:
    geojson = json.load(f)

for feat in geojson.get("features", []):
    props = feat.get("properties", {})
    name = props.get("DistName") or props.get("NAME") or props.get("name", "")
    geom = feat.get("geometry", {})
    
    coords = geom.get("coordinates", [])
    if geom.get("type") == "MultiPolygon" and coords:
        ring = coords[0][0]
    elif geom.get("type") == "Polygon" and coords and len(coords) > 0 and len(coords[0]) > 0:
        ring = coords[0]
    else:
        ring = []
    
    if ring and len(ring) > 0:
        clng = sum(p[0] for p in ring) / len(ring)
        clat = sum(p[1] for p in ring) / len(ring)
        print(f"Name in geojson: {name}, clng: {clng:.4f}, clat: {clat:.4f}")
