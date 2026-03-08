import json
import math
import urllib.request
import urllib.parse
from pathlib import Path

# WGS84 to GCJ02 Conversion
pi = 3.1415926535897932384626
a = 6378245.0
ee = 0.00669342162296594323

def transformLat(x, y):
    ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(math.fabs(x))
    ret += (20.0 * math.sin(6.0 * x * pi) + 20.0 * math.sin(2.0 * x * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(y * pi) + 40.0 * math.sin(y / 3.0 * pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(y / 12.0 * pi) + 320 * math.sin(y * pi / 30.0)) * 2.0 / 3.0
    return ret

def transformLon(x, y):
    ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(math.fabs(x))
    ret += (20.0 * math.sin(6.0 * x * pi) + 20.0 * math.sin(2.0 * x * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(x * pi) + 40.0 * math.sin(x / 3.0 * pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(x / 12.0 * pi) + 300.0 * math.sin(x / 30.0 * pi)) * 2.0 / 3.0
    return ret

def wgs84_to_gcj02(lng, lat):
    """WGS84转GCJ02"""
    dLat = transformLat(lng - 105.0, lat - 35.0)
    dLon = transformLon(lng - 105.0, lat - 35.0)
    radLat = lat / 180.0 * pi
    magic = math.sin(radLat)
    magic = 1 - ee * magic * magic
    sqrtMagic = math.sqrt(magic)
    dLat = (dLat * 180.0) / ((a * (1 - ee)) / (magic * sqrtMagic) * pi)
    dLon = (dLon * 180.0) / (a / sqrtMagic * math.cos(radLat) * pi)
    return lng + dLon, lat + dLat

def transform_coords_recursive(coords):
    if not isinstance(coords, list):
        return coords
    if len(coords) == 2 and isinstance(coords[0], (int, float)) and isinstance(coords[1], (int, float)):
        return list(wgs84_to_gcj02(coords[0], coords[1]))
    return [transform_coords_recursive(c) for c in coords]

def fetch_zhutian():
    town = "珠田乡"
    query = f"{town},万年县，江西省，中国"
    encoded = urllib.parse.quote(query)
    nominatim_url = f"https://nominatim.openstreetmap.org/search?format=json&q={encoded}&polygon_geojson=1"
    try:
        req = urllib.request.Request(nominatim_url, headers={"User-Agent": "YiyangEVProject/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            results = json.loads(response.read().decode('utf-8'))
        
        if results and 'geojson' in results[0]:
            print(f"fetch {town} success")
            return {
                "type": "Feature",
                "properties": {"DistName": town, "NAME": town, "name": town},
                "geometry": results[0]['geojson']
            }
        else:
            print("no polygon for zhutian, just center")
    except Exception as e:
        print(f"failed to fetch {town}: {e}")
    return None

import os
data_dir = Path(r"c:\Users\lhn\OneDrive\Desktop\江西\弋阳充电桩项目\data")
in_file = data_dir / "wannian_townships.geojson"
out_file = data_dir / "wannian_townships_fixed.geojson"

with open(in_file, "r", encoding="utf-8") as f:
    geojson = json.load(f)

# fetch zhutian and add
zhutian_feat = fetch_zhutian()
if zhutian_feat:
    geojson["features"].append(zhutian_feat)

# filter out nanxi and transform
fixed_features = []
print("Starting transform...")
for feat in geojson["features"]:
    name = feat.get("properties", {}).get("name", "")
    if "南溪" in name:
        continue # skip invalid town for wannian
    
    # transform geometry WGS84 -> GCJ02
    geom = feat["geometry"]
    if "coordinates" in geom:
        geom["coordinates"] = transform_coords_recursive(geom["coordinates"])
    
    fixed_features.append(feat)

geojson["features"] = fixed_features

with open(out_file, "w", encoding="utf-8") as f:
    json.dump(geojson, f, ensure_ascii=False)

print("done writing geojson, computing centroids...")

townships_corrected = []
for feat in fixed_features:
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
        townships_corrected.append({"name": name, "lng": round(clng, 4), "lat": round(clat, 4)})

print(townships_corrected)

# Update app.py
app_file = Path(r"c:\Users\lhn\OneDrive\Desktop\江西\弋阳充电桩项目\app.py")
with open(app_file, "r", encoding="utf-8") as f:
    app_code = f.read()

import re
replacement = "wannian_townships = [\n"
for t in townships_corrected:
    replacement += f'            {{"name": "{t["name"]}", "lng": {t["lng"]}, "lat": {t["lat"]}}},\n'
replacement += "        ]"

# replace the list
app_code = re.sub(r'wannian_townships\s*=\s*\[.*?\]', replacement, app_code, flags=re.DOTALL)

with open(app_file, "w", encoding="utf-8") as f:
    f.write(app_code)

print("app.py updated")
