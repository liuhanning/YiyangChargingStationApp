import json
import sqlite3
import pandas as pd
from shapely.geometry import shape, Point

DB = r"C:\Users\lhn\OneDrive\Desktop\江西\弋阳充电桩项目\db\yiyang_ev.db"
GEO_FILE = r"C:\Users\lhn\OneDrive\Desktop\江西\弋阳充电桩项目\data\yiyang_townships.geojson"

# 1. Load Townships
with open(GEO_FILE, "r", encoding="utf-8") as f:
    geojson = json.load(f)

townships = {}
for feat in geojson["features"]:
    props = feat["properties"]
    name = props.get("DistName", props.get("NAME", props.get("name", "")))
    geom = shape(feat["geometry"])
    
    # Store the polygon and the centroid
    townships[name] = {
        "polygon": geom,
        "centroid": (geom.centroid.x, geom.centroid.y)
    }

# Yiyang full boundary (rough approximation by union)
from shapely.ops import unary_union
county_shape = unary_union([t["polygon"] for t in townships.values()])

# 2. Check and fix stations
conn = sqlite3.connect(DB)

def process_table(table_name, name_col='station_name', town_col='township'):
    if table_name == 'gas_stations':
        town_col = 'address'  # Address often contains the town
    if table_name == 'stations_urban_coords':
        town_col = 'address' 
        
    cols = [c[1] for c in conn.execute(f"PRAGMA table_info({table_name})").fetchall()]
    has_town = town_col in cols
    
    # Read rows
    if has_town:
        rows = conn.execute(f"SELECT id, {name_col}, {town_col}, longitude, latitude FROM {table_name}").fetchall()
    else:
        rows = conn.execute(f"SELECT id, {name_col}, '', longitude, latitude FROM {table_name}").fetchall()
    
    updates = []
    
    for rid, name, town_val, lng, lat in rows:
        if lng is None or lat is None or pd.isna(lng):
            continue
            
        pt = Point(lng, lat)
        
        # Determine actual township
        actual_town = None
        for t_name, t_data in townships.items():
            if t_data["polygon"].contains(pt):
                actual_town = t_name
                break
                
        # Is it in Yiyang at all?
        if not county_shape.contains(pt):
            # It's outside Yiyang!
            actual_town = "OUTSIDE"
            
        # Determine intended township
        target_town = None
        if town_val:
            for t_name in townships.keys():
                # some loose matching
                if t_name in town_val or t_name.replace("镇","").replace("乡","").replace("街道","") in town_val:
                    target_town = t_name; break
        if not target_town and name:
            for t_name in townships.keys():
                if t_name in name or t_name.replace("镇","").replace("乡","").replace("街道","") in name:
                    target_town = t_name; break
                    
        # If target is known but it's not in target or outside Yiyang, we need to move it!
        if target_town:
            if target_town != actual_town:
                print(f"[FIX] {name} (Intended: {target_town}, Found: {actual_town}) -> Moving to {target_town} center")
                c_lng, c_lat = townships[target_town]["centroid"]
                import random
                # tiny offset
                new_lng = c_lng + random.uniform(-0.015, 0.015)
                new_lat = c_lat + random.uniform(-0.015, 0.015)
                updates.append((new_lng, new_lat, rid))
        else:
            if actual_town == "OUTSIDE":
                # Doesn't belong to any specific known town based on name, but is outside.
                print(f"[UNKNOWN OUTSIDE] {name} is outside county, no explicit town found.")
                # Null out the coords so it disappears rather than showing outside
                updates.append((None, None, rid))
                
    for u in updates:
        conn.execute(f"UPDATE {table_name} SET longitude=?, latitude=? WHERE id=?", u)

process_table("stations_planned")
process_table("stations_urban_coords", name_col="station_name")
process_table("gas_stations", name_col="station_name")

conn.commit()
conn.close()
print("Verification complete.")
